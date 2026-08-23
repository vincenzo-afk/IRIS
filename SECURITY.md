# Security Policy

## Scope

IRIS can capture screen content, record microphone input, read the clipboard, send data to configured third-party services, fetch web pages, and control mouse and keyboard input. Treat it as a privileged desktop application and run it only in environments where those capabilities are appropriate.

## Supported versions

There is no published release series yet. Security fixes should be reported against the current `main` branch.

## Reporting a vulnerability

Please do not disclose exploitable details in a public issue. Contact the repository owner, [@vincenzo-afk](https://github.com/vincenzo-afk), through a private GitHub channel and include a concise description, affected files or modes, reproduction steps, impact, and any suggested mitigation. Remove API keys, personal data, screen captures, audio, clipboard contents, and other secrets from reports.

If a private reporting channel is not available, open a minimal public issue that contains no exploit details and asks the maintainer for a private contact path.

## Security practices for contributors

Keep credentials in `.env`, never commit runtime data, and document any new network request, external service, permission, or computer-control behavior. Changes to autonomous actions should include a clear safety explanation and manual validation notes.
