# Validation

Recorded 2026-09-18.

## Automated

- Ten fake-CLI unit tests passed locally on macOS with Python 3.13.
- Tests cover read-only/edit tool selection, literal stdin, auth failure, required-flag checks, malformed/empty/error/nonzero results, permission denials, timeout, SIGTERM worker cleanup, status identity minimization, and missing executable.
- Plugin manifest and skill validators passed before publication.
- Independent source review found a SIGTERM cleanup gap in development. It was fixed, regression-tested and re-reviewed.
- GitHub Actions is configured for macOS/Linux with Python 3.10/3.13. Check the Actions tab for current CI outcomes.

## Live model run

- Official Claude Code CLI 2.1.277, authenticated via claude.ai.
- Requested model and returned modelUsage: `claude-fable-5-1`.
- Edit run completed with exit 0 and no permission denials.
- Created the included standalone HTML focus timer.
- Desktop 1440x1000 and mobile 390x844 screenshots inspected.
- Host checked timer start/pause/reset/completion, one-time session counting, keyboard tabs, suggestion rotation, text-safe input and persistence, duplicate IDs, overflow and JavaScript errors.
- Host made Kuwaiti wording changes only. Original model output is included.
- Sanitized receipt: [examples/khalwa/validation.json](examples/khalwa/validation.json).

## Limits

One live edit run verifies integration, not comparative model quality. Model identity is CLI-reported, not an independent server attestation. Read-only mode is covered by fake tests but has not separately been live-model tested. Windows is unsupported. Tool restrictions are not an OS sandbox. Account access, CLI flags and model availability can change.
