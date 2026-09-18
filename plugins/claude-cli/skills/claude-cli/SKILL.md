---
name: claude-cli
description: Delegate a scoped review or file-editing task from Codex to the official local Claude Code CLI when the user asks to use Claude, get Claude's second opinion, or hand Claude implementation work. Not for ordinary tasks or autonomous repeated review loops.
---
# Claude CLI

Use the runner at `../../scripts/bridge.py`, resolved relative to this SKILL.md. Use an absolute runner path in commands. Requires Python 3.10+ and authenticated official Claude Code CLI with `--safe-mode` support. This is a personal integration, not an Anthropic plugin.

## Handoff

1. Preserve the user's scope and authorization. Choose one bounded task. For edits, assign exact owned files; do not edit them concurrently. Prefer an isolated checkout if the working tree has unrelated changes.
2. Write the task to a private temporary UTF-8 file. Include outcome, source files, relevant host/project policies, constraints, acceptance checks and output expectations. Do not copy credentials or unrelated conversation history. Include the relevant diff as text for a code review: the worker has no shell. Safe mode disables automatic CLAUDE.md, skills, plugins, hooks and MCP. Supply policy explicitly.
3. Run `python3 <absolute-runner> status --cwd <absolute-workspace>`. If authentication is missing, ask the user to sign in manually with `claude auth login`. Never read or copy credentials, automate login, or change providers to bypass this.
4. Run `python3 <absolute-runner> run --cwd <absolute-workspace> --prompt-file <task-file>`. Default mode is `review`, exposing only Read/Glob/Grep. Add `--mode edit` only for authorized file changes; this adds Edit/Write, never Bash or network tools. The tool list is not an OS filesystem sandbox. Keep access and ownership scoped in the work order.
5. Omit `--model` and `--effort` unless the user explicitly selected them. Do not change global model settings. The result separates requested model from observed modelUsage. If observed metadata is absent, say it is unknown. Do not claim the host's model carries over.
6. Use the host's asynchronous shell session support for long runs and poll with bounded waits. Tasks have no runtime deadline by default. Do not add `--timeout` unless the user explicitly requests a task time limit; `--timeout 0` also means unlimited. Bounded polling waits must not terminate the worker. An explicitly requested timeout or user cancellation stops the child process group and may leave partial edits. Inspect them before retrying. There is no automatic retry or fallback.
7. Parse returned JSON and check the process exit code. `incomplete`, permission denials, invalid JSON, or error are not completion. Preserve useful partial output and explain the blocker. Do not expand permissions to make a blocked run pass.
8. Codex inspects the actual diff, runs relevant acceptance checks, and adjudicates findings. A worker's `completed` only confirms a successful CLI result, never verified correctness. Do not blindly apply review advice.
9. Remove the temporary task file after consuming the output. Present changed files, host checks, unresolved risks, and actual usage if requested. Report cost as CLI-reported accounting, not necessarily an extra subscription charge.

## Examples

- Ask Claude to review this change for edge cases without editing anything.
- Have Claude implement the parser in the named files, then run the tests yourself.

Each run is fresh and non-resumable. The session ID is diagnostic only. Version one deliberately leaves shell checks, external integrations, publishing and commits with the host, under existing user authorization.
