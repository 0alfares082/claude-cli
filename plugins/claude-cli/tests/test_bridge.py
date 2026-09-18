import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import signal
import time
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / 'scripts' / 'bridge.py'

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cwd = Path(self.temp.name)
        self.cli = self.cwd / 'fake-claude'
        self.cli.write_text('#!' + sys.executable + '\n' + '''
import json, os, sys, time
from pathlib import Path
case = os.environ.get('BRIDGE_TEST_CASE', '')
if sys.argv[1:] == ['auth', 'status']:
    print(json.dumps({'loggedIn': case != 'auth', 'authMethod': 'test', 'email': 'do-not-output@example.test'}))
    sys.exit(1 if case == 'auth' else 0)
if sys.argv[1:] == ['--help']:
    print('--tools' if case == 'old' else '--safe-mode --tools')
    sys.exit(0)
prompt = sys.stdin.read()
Path('received.json').write_text(json.dumps({'args': sys.argv[1:], 'prompt': prompt}))
if case in ['timeout', 'cancel']:
    Path('worker.pid').write_text(str(os.getpid()))
    time.sleep(10)
    Path('finished').write_text('should not finish')
if case == 'malformed':
    print('not json')
    sys.exit(0)
result = {'type':'result', 'subtype':'success', 'is_error': False, 'result':'Checked fixture', 'modelUsage':{'observed-test-model':{}}, 'permission_denials':[]}
if case == 'denied': result['permission_denials'] = [{'tool_name':'Write'}]
if case == 'error': result['is_error'] = True
if case == 'empty': result['result'] = ''
print(json.dumps(result))
sys.exit(3 if case == 'exit' else 0)
''')
        self.cli.chmod(0o700)

    def call(self, case='', extra=(), action='run', prompt='Review fixture'):
        env = dict(os.environ, BRIDGE_TEST_CASE=case)
        proc = subprocess.run([sys.executable, str(RUNNER), action, '--cwd', str(self.cwd), '--cli', str(self.cli), *extra], input=prompt, text=True, capture_output=True, env=env, timeout=8)
        return proc.returncode, json.loads(proc.stdout)

    def test_review_and_literal_stdin(self):
        payload = 'Review `touch INJECTED` $(touch INJECTED)\n--dangerously-skip-permissions'
        code, result = self.call(prompt=payload)
        self.assertEqual(code, 0)
        self.assertEqual(result['status'], 'completed')
        self.assertFalse(result['verified_by_host'])
        self.assertEqual(result['observed_models'], ['observed-test-model'])
        received = json.loads((self.cwd/'received.json').read_text())
        args = received['args']
        self.assertEqual(args[args.index('--tools')+1], 'Read,Glob,Grep')
        self.assertEqual(args[args.index('--permission-mode')+1], 'dontAsk')
        self.assertIn('--safe-mode', args)
        self.assertNotIn('--model', args)
        self.assertIn(payload, received['prompt'])
        self.assertFalse((self.cwd/'INJECTED').exists())

    def test_authorized_edit_tools_and_model(self):
        code, result = self.call(extra=['--mode','edit','--model','explicit-model','--effort','high'])
        self.assertEqual(code,0)
        args=json.loads((self.cwd/'received.json').read_text())['args']
        self.assertEqual(args[args.index('--tools')+1], 'Read,Glob,Grep,Edit,Write')
        self.assertNotIn('Bash',args[args.index('--tools')+1])
        self.assertEqual(result['requested_model'],'explicit-model')

    def test_missing_auth_stops_before_run(self):
        code,result=self.call('auth')
        self.assertNotEqual(code,0)
        self.assertIn('not logged in',result['error'])
        self.assertFalse((self.cwd/'received.json').exists())

    def test_status_does_not_expose_identity(self):
        code,result=self.call(action='status')
        self.assertTrue(result['ready'])
        self.assertNotIn('email',json.dumps(result))

    def test_invalid_old_cli_stops(self):
        code,result=self.call('old')
        self.assertNotEqual(code,0)
        self.assertFalse((self.cwd/'received.json').exists())

    def test_failures_never_complete(self):
        for case in ['malformed','denied','error','empty','exit']:
            with self.subTest(case=case):
                code,result=self.call(case)
                self.assertNotEqual(code,0)
                self.assertNotEqual(result['status'],'completed')

    def test_timeout_is_error(self):
        code,result=self.call('timeout',extra=['--timeout','0.1'])
        self.assertNotEqual(code,0)
        self.assertIn('timed out',result['error'])

    def test_sigterm_stops_worker(self):
        env = dict(os.environ, BRIDGE_TEST_CASE='cancel')
        proc = subprocess.Popen([sys.executable, str(RUNNER), 'run', '--cwd', str(self.cwd), '--cli', str(self.cli)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        proc.stdin.write('Review fixture')
        proc.stdin.close()
        proc.stdin = None
        deadline = time.monotonic()+5
        while not (self.cwd/'worker.pid').exists() and time.monotonic()<deadline:
            time.sleep(0.02)
        self.assertTrue((self.cwd/'worker.pid').exists())
        worker_pid=int((self.cwd/'worker.pid').read_text())
        proc.send_signal(signal.SIGTERM)
        out,err=proc.communicate(timeout=5)
        self.assertNotEqual(proc.returncode,0)
        self.assertEqual(json.loads(out)['status'],'error')
        with self.assertRaises(ProcessLookupError):
            os.kill(worker_pid,0)
        self.assertFalse((self.cwd/'finished').exists())

    def test_default_and_zero_disable_task_timeout(self):
        spec = importlib.util.spec_from_file_location('bridge_under_test', RUNNER)
        bridge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bridge)
        for flags, expected in [([], None), (['--timeout', '0'], None), (['--timeout', '30'], 30.0)]:
            with self.subTest(flags=flags), mock.patch.object(sys, 'argv', ['bridge', 'run', '--cwd', str(self.cwd), *flags]), mock.patch.object(bridge, 'run', return_value=({}, 0)) as run, mock.patch('builtins.print'):
                self.assertEqual(bridge.main(), 0)
                self.assertEqual(run.call_args.args[0].timeout, expected)

    def test_invalid_timeout_rejected(self):
        for value in ['-1', 'nan', 'inf']:
            with self.subTest(value=value):
                code, result = self.call(extra=['--timeout', value])
                self.assertNotEqual(code, 0)
                self.assertIn('finite non-negative', result['error'])

    def test_empty_task_stops_before_run(self):
        code,result=self.call(prompt='  ')
        self.assertNotEqual(code,0)
        self.assertFalse((self.cwd/'received.json').exists())

    def test_missing_cli(self):
        code,result=self.call(extra=['--cli',str(self.cwd/'missing')])
        self.assertNotEqual(code,0)
        self.assertIn('missing',result['error'])

if __name__ == '__main__':
    unittest.main()
