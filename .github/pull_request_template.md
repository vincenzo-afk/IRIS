## Summary

Describe the problem, user-facing change, and implementation.

## Validation

List the exact commands and manual scenarios used, including the environment when relevant.

- [ ] `python -m compileall -q core overlay tools main.py config.py`
- [ ] Manual validation completed where desktop permissions, audio, screen capture, or automation are involved.

## Documentation

- [ ] README or other documentation updated when behavior, setup, configuration, or permissions changed.

## Risk review

- Breaking changes:
- New permissions or network requests:
- Secrets or personal screen/audio/clipboard/task data excluded:
- Computer-control safety considerations:

## Checklist

- [ ] The change is narrowly scoped.
- [ ] No API keys, credentials, captures, logs, or runtime data are committed.
- [ ] The pull request is ready for review.
