# Contributing

Thank you for contributing to Claude CLI.

## Before making a change

- Open an issue for substantial behavior changes.
- Keep documentation, issue reports, and pull requests in English.
- Never include credentials, private prompts, mailbox content, or account tokens.
- Preserve scoped tool permissions, manual authentication, and honest result reporting.
- Do not add a default task deadline. Time limits must be explicitly requested.

## Local checks

Use Python 3.10 or newer on macOS or Linux:

```sh
python3 -m unittest discover -s plugins/claude-cli/tests -v
git diff --check
```

Tests use a fake Claude executable and do not consume model quota. Add regression tests for behavior changes. Distinguish unit-test results from actual Claude integration runs, and document any live validation without exposing private data.

## Pull requests

Describe the problem, your change, and the checks you ran. Keep changes focused. Do not edit historical model outputs or validation screenshots to imply a test was performed when it was not.

The maintainer is [Salman AlFares](https://github.com/0alfares082). GitHub tracks contributors from committed changes; do not add invented contributors or imply vendor endorsement.
