# Contributing to IRIS

Thank you for contributing to IRIS. The project is a local Python desktop assistant, so changes should prioritize predictable behavior, explicit permissions, and clear documentation of any screen, microphone, clipboard, network, or computer-control effects.

## Development setup

Use the repository setup script to create a virtual environment and install dependencies:

```bash
bash setup.sh
source venv/bin/activate
```

Copy `.env.example` to `.env` and provide a Gemini API key before exercising AI-backed functionality. Keep `.env`, logs, screenshots, audio files, and local task data out of commits.

## Validation

Run the syntax check before opening a pull request:

```bash
python -m compileall -q core overlay tools main.py config.py
```

There is currently no automated end-to-end test suite. If your change affects desktop automation, voice input, screen capture, third-party APIs, or the overlay, describe the manual validation environment and steps in the pull request.

## Workflow

Create a focused branch from `main`. Use a short, descriptive branch name such as `fix/audio-fallback` or `docs/setup-guide`. Keep pull requests small enough to review and explain the motivation, implementation, validation performed, user-visible changes, and any security or privacy implications.

Do not commit API keys, personal captures, generated runtime directories, or unrelated formatting changes. If a change adds a dependency or changes an environment variable, update `requirements.txt`, `.env.example`, and `README.md` together.

## Pull requests

A pull request should include:

- A concise explanation of the problem and solution.
- The exact validation command or manual scenario used.
- Documentation updates for changed commands, modes, configuration, or behavior.
- A note describing any breaking change, new permission, network request, or secret requirement.

Use clear commit subjects in the imperative mood, for example `Improve voice fallback handling` or `Document local memory setup`. The repository does not currently enforce a formal commit-message tool.

## Issues

Before opening an issue, search existing issues and include the operating system, Python version, selected IRIS mode, relevant logs with secrets removed, and reproducible steps. Do not publish credentials or sensitive screen, microphone, clipboard, or task data.
