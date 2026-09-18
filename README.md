# Claude CLI

**Ask Claude Code to review or edit files without leaving Codex.**

[![Tests](https://github.com/0alfares082/claude-cli/actions/workflows/tests.yml/badge.svg)](https://github.com/0alfares082/claude-cli/actions)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)](plugins/claude-cli/scripts/bridge.py)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Install](#install) · [Usage](#use-it) · [Source code](plugins/claude-cli/scripts/bridge.py) · [Validation](VALIDATION.md) · [Contributing](CONTRIBUTING.md)

Claude CLI is a community-built Codex plugin that calls the **official Claude Code CLI** on your machine. Codex scopes the task, Claude does the delegated work, and Codex checks the result.

It is not an official Anthropic or OpenAI product. It does not embed Claude's source code or share the author's account.

## At a glance

| Component | Details |
| --- | --- |
| Claude integration | Official local Claude Code CLI, authenticated to your own account |
| Host | Codex |
| Implementation | Python 3.10+, standard library only |
| Supported systems | macOS and Linux |
| Task duration | No time limit by default |
| Maintainer | [Salman AlFares](https://github.com/0alfares082) |
| License | MIT |

The [validation record](VALIDATION.md) documents tests and a live Fable 5.1 integration run. Historical generated artifacts are retained under `examples/`; they are not the plugin interface or a model-quality benchmark.

## Install

You need:

- macOS or Linux and Python 3.10+. Windows is not supported by this runner's POSIX process-group cleanup.
- Codex with plugin and marketplace support, running locally with shell access.
- The [official Claude Code CLI](https://code.claude.com/docs/en/setup), authenticated to your own account, with `--safe-mode` support. The live example used version `2.1.277`.
- Access to whichever Claude model you request. Fable 5.1 needs Claude Code `2.1.257` or later.

Check your CLI and sign in if needed:

```sh
claude --version
claude auth status
claude auth login
```

Then install the plugin:

```sh
codex plugin marketplace add 0alfares082/claude-cli
codex plugin add claude-cli@claude-cli
```

**Start a new Codex task** so the plugin's skill is loaded. If your Codex CLI does not recognize the plugin commands, update Codex first. This is a machine-local integration, not a hosted web connector.

## Use it

Ask Codex in plain language:

```text
Use Claude CLI to review my current changes for edge cases. Do not edit anything.
```

```text
Use Claude CLI with claude-fable-5-1 to build a standalone index.html
for a focus timer. Claude owns only index.html. Then inspect the result
and test it in the browser yourself.
```

```text
Have Claude CLI review this plan. Give it the requirements and relevant
source files, and return concrete issues with file references.
```

You can also mention `$claude-cli` explicitly. Model and effort are omitted by default; explicit choices apply only to that run and do not change global model settings.

## What happens

```text
You -> Codex scopes the task -> official Claude Code CLI -> result + files
         ^                                                    |
         +--------- Codex inspects and runs checks -----------+
```

1. Codex writes a scoped work order, including relevant project rules.
2. The runner checks CLI authentication and required isolation flags.
3. Claude receives the prompt over stdin and returns JSON.
4. Codex reads the result, inspects actual changes, and runs acceptance checks.

| Mode | Available tools | Use |
| --- | --- | --- |
| `review` (default) | `Read`, `Glob`, `Grep` | Independent review and diagnosis |
| `edit` | The above plus `Edit`, `Write` | Explicitly authorized file changes |

Claude has no Bash, browser, MCP, hooks, skills, or other customizations in this run. Codex runs shell tests separately. Global/project instructions are not auto-loaded in safe mode, so the host must pass the relevant rules explicitly.

These are CLI tool restrictions, **not an operating-system filesystem sandbox**. Use trusted workspaces, provide precise file ownership, and use an isolated checkout when appropriate.

## Standalone runner

After cloning this repository:

```sh
python3 plugins/claude-cli/scripts/bridge.py status --cwd /absolute/project

python3 plugins/claude-cli/scripts/bridge.py run \
  --cwd /absolute/project \
  --prompt-file /absolute/task.txt

python3 plugins/claude-cli/scripts/bridge.py run \
  --cwd /absolute/project \
  --mode edit \
  --model claude-fable-5-1 \
  --prompt-file /absolute/task.txt
```

The prompt can also come through stdin. Optional flags: `--cli`, `--model`, `--effort`, and `--timeout`. Tasks have **no time limit by default**. `--timeout 0` also disables the task deadline. Only pass a positive number of seconds when the user explicitly requests a time limit. Short authentication/help probes still have their own 20-second limits; these do not limit the Claude task.

The JSON reports requested and observed models separately, permission denials, usage, and the CLI exit status. `completed` means the CLI returned a successful result; it does not prove the code is correct. `verified_by_host` stays false in the runner output because host verification is a separate step.

## Boundaries and troubleshooting

- **Authentication:** log in manually using the official CLI. The plugin does not extract, copy, store or automate login credentials.
- **Usage:** requests use your configured Claude account/provider and its limits or billing. It does not make model access free. CLI-reported dollar accounting does not necessarily mean a separate subscription charge. Fable can use usage credits on some accounts; check your account settings.
- **Missing access or model error:** the runner fails rather than selecting another model. Observed model metadata comes from the CLI, not from asking Claude to identify itself.
- **Permission denied:** reported as incomplete. The runner does not retry with broader permissions.
- **Timeout/cancellation:** the child process group is stopped. Partial edits may remain; inspect them before retrying. Force-killing the wrapper with SIGKILL cannot run cleanup.
- **Fresh runs:** no continuation or automatic retry. Session IDs are diagnostic only; session persistence is disabled.
- **Privacy:** the work order and files Claude reads are processed by your configured Claude service. No additional telemetry endpoint is implemented by this plugin. Keep credentials and unrelated personal context out of work orders.
- **No response until completion:** this version collects the final JSON; it does not stream model progress.

## Development

No Python packages are required for the runner or its unit tests.

```sh
python3 -m unittest discover -s plugins/claude-cli/tests -v
```

Tests use fake CLI processes and consume no model quota. CI runs the same suite on macOS and Linux. See [VALIDATION.md](VALIDATION.md) for what has actually been verified.

## Uninstall

```sh
codex plugin remove claude-cli@claude-cli
```

## Credits and license

Created by Salman AlFares. [MIT](LICENSE).

Built against the [official CLI reference](https://code.claude.com/docs/en/cli-reference) and [programmatic-use documentation](https://code.claude.com/docs/en/headless).

## Source and contributors

- [Python runner](plugins/claude-cli/scripts/bridge.py): authentication checks, scoped delegation, cancellation, and result handling.
- [Tests](plugins/claude-cli/tests/test_bridge.py): fake-CLI tests that consume no model quota.
- [Skill instructions](plugins/claude-cli/skills/claude-cli/SKILL.md): the handoff contract used by Codex.
- [Plugin manifest](plugins/claude-cli/.codex-plugin/plugin.json): plugin metadata and entry points.
- [Contributors](https://github.com/0alfares082/claude-cli/graphs/contributors): GitHub's commit-based contributor history.

Claude is the integrated coding tool, not a human maintainer. Contributions are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).
