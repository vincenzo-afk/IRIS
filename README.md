# IRIS

> **Intelligent Real-time Interactive System** — a Python desktop AI assistant that combines screen awareness, voice interaction, persistent memory, and optional computer automation.

```text
██╗██████╗ ██╗███████╗
██║██╔══██╗██║██╔════╝
██║██████╔╝██║███████╗
██║██╔══██╗██║██╔════╝
██║██║  ██║██║███████║
╚═╝╚═╝  ╚═╝╚═╝╚══════╝
Intelligent Real-time Interactive System
```

[![Python](https://img.shields.io/badge/python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Repository](https://img.shields.io/badge/GitHub-vincenzo--afk%2FIRIS-181717?logo=github)](https://github.com/vincenzo-afk/IRIS)

[Report a bug](https://github.com/vincenzo-afk/IRIS/issues/new) · [Request a feature](https://github.com/vincenzo-afk/IRIS/issues/new) · [View the source](https://github.com/vincenzo-afk/IRIS)

## <a name="table-of-contents"></a>Table of Contents

- [About the Project](#about-the-project)
- [Current Status](#current-status)
- [Architecture](#architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage](#usage)
- [Agent Tools](#agent-tools)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Security and Privacy](#security-and-privacy)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## <a name="about-the-project"></a>About the Project

IRIS is a local desktop assistant organized around a small set of cooperating Python modules. It can capture and describe the current screen through Gemini, accept typed or spoken requests, retain relevant memories through Mem0, display cursor-following explanations in a Tkinter overlay, and execute selected desktop actions through `pyautogui` and `pynput`.

The main entry point, `main.py`, exposes five operational modes. `WATCH` continuously analyzes the screen, `CHAT` provides text conversation with screen and memory context, `TEACH` explains the interface near the cursor, `DO` runs an autonomous task loop with Gemini function calling, and `VOICE` listens for the configured wake phrase before routing commands to chat or task execution.

IRIS has direct access to the screen, microphone, clipboard, keyboard, mouse, and selected web content when the corresponding mode is running. Use it only on a machine and account where you are comfortable granting those permissions, and review tasks before allowing computer-control actions.

## <a name="current-status"></a>Current Status

This repository is an early-stage desktop application rather than a packaged release. The implementation includes the core modules described below, but it does not currently include a release artifact, Docker configuration, database migration system, automated test suite, or published license.

The setup script is Unix-oriented, while parts of the application contain platform-specific branches for Linux, macOS, and Windows. Hardware permissions, desktop-session configuration, audio drivers, available applications, API quotas, and third-party package compatibility can affect runtime behavior.

## <a name="architecture"></a>Architecture

```mermaid
flowchart TD
    CLI[main.py\nmode selector] --> MODES{Operational mode}
    MODES --> WATCH[ScreenWatcher]
    MODES --> CHAT[Text chat]
    MODES --> TEACH[TeachMode + Tkinter overlay]
    MODES --> DO[IRISAgent]
    MODES --> VOICE[VoiceListener]

    WATCH --> VISION[core/vision.py]
    CHAT --> AGENT[core/agent.py chat()]
    DO --> AGENT
    VOICE --> STT[faster-whisper STT]
    VOICE --> AGENT
    TEACH --> VISION

    VISION --> GEMINI[Google Gemini API]
    AGENT --> GEMINI
    AGENT --> AUTOMATION[core/automation.py\npyautogui + pynput]
    AGENT --> WEB[web_search + scrape_url]
    AGENT --> TASKS[data/tasks.json]
    AGENT --> MEMORY[core/memory.py]
    MEMORY --> MEM0[Mem0 local/Qdrant or cloud]
    VOICE --> TTS[pyttsx3 / ElevenLabs / gTTS]
```

The autonomous loop observes the screen, builds relevant memory context, sends a goal to Gemini with the available function declarations, executes returned tools, optionally captures a verification screenshot, and repeats until the model reports completion or the configured step limit is reached.

## <a name="features"></a>Features

| Capability | Implementation status | Evidence in the repository |
|---|---|---|
| Screen capture and description | Implemented | `core/vision.py` uses `mss` when available and falls back to `PIL.ImageGrab`; Gemini generates descriptions. |
| Screen text extraction | Implemented | `read_text_on_screen()` sends a screenshot to Gemini with an OCR-like extraction prompt. |
| Natural-language element location | Implemented | `find_element()` asks Gemini for an approximate position or `NOT FOUND`. |
| Background screen watching | Implemented | `ScreenWatcher` captures and caches descriptions at the configured interval. |
| Text chat | Implemented | `chat()` injects memory and optional current-screen context without tool calling. |
| Autonomous computer control | Implemented | `IRISAgent` can call mouse, keyboard, application, clipboard, web, and task tools. |
| Voice input | Implemented | `faster-whisper` transcribes microphone recordings on CPU using `int8` computation. |
| Voice output | Implemented | `pyttsx3` is the default; ElevenLabs and gTTS paths are available in `core/voice.py`. |
| Wake-word interaction | Implemented | `VoiceListener` detects the configured `hey iris` phrase before recording a command. |
| Cursor-following teaching overlay | Implemented | `overlay/cursor_widget.py` and `overlay/teach_mode.py` provide a Tkinter overlay. |
| Persistent memory | Implemented with backend requirements | `core/memory.py` supports Mem0 Cloud and local Qdrant-backed configuration. |
| Lightweight task persistence | Implemented | `tools/task_tools.py` stores pending tasks in `data/tasks.json`. |
| Automated regression tests | Not present | No test directory or test files are currently included. |
| Packaged deployment | Not present | No Dockerfile, compose file, installer, or release workflow is included. |

## <a name="technology-stack"></a>Technology Stack

| Area | Technologies used |
|---|---|
| Runtime | Python 3, standard-library threading, logging, argparse, and filesystem APIs |
| Multimodal AI | `google-generativeai`; model names are configured in `config.py` |
| Screen vision | `mss`, Pillow, Gemini vision prompts, JPEG/base64 encoding |
| Computer automation | `pyautogui`, `pynput`, clipboard helpers, and platform-specific process/window helpers |
| Speech-to-text | `faster-whisper`, `sounddevice`, `soundfile`, NumPy |
| Text-to-speech | `pyttsx3` by default, with optional ElevenLabs and gTTS branches |
| Memory | `mem0ai`, local Qdrant configuration, or Mem0 Cloud |
| Web access | `duckduckgo-search`, `requests`, and BeautifulSoup |
| Overlay UI | Tkinter and `pynput` cursor tracking |
| Local persistence | JSON task file at `data/tasks.json`, created at runtime |

The dependency specifications are maintained in [`requirements.txt`](requirements.txt). They use minimum versions for most packages and exact pins for `opencv-python-headless` and `av`; they are not a lockfile.

<details>
<summary>Complete dependency specification</summary>

```text
google-generativeai>=0.8.0
mem0ai>=0.1.0
pyautogui>=0.9.54
pynput>=1.7.6
mss>=9.0.1
Pillow>=10.0.0
faster-whisper>=1.0.0
elevenlabs>=1.0.0
pyttsx3>=2.90
opencv-python-headless==4.8.1.78
sounddevice>=0.4.6
soundfile>=0.12.1
numpy>=1.24.0
python-dotenv>=1.0.0
pyperclip>=1.8.2
gTTS>=2.5.0
pygame>=2.5.0
av==13.1.0
duckduckgo-search>=6.0.0
beautifulsoup4>=4.12.0
requests>=2.30.0
```
</details>

## <a name="getting-started"></a>Getting Started

### Prerequisites

You need Python 3 available as `python3`, a working desktop session, and permission for any capabilities you intend to use. Voice modes require an accessible microphone and audio output. Screen and computer-control modes require a desktop environment in which `mss`, `PIL.ImageGrab`, `pyautogui`, and `pynput` can operate.

A Google Gemini API key is required for the screen, chat, agent, and memory flows. Mem0 Cloud and ElevenLabs keys are optional according to the current configuration. Local memory mode also expects a Qdrant service at `localhost:6333` when the Mem0 local client is successfully initialized.

### Installation

The repository includes the following setup script:

```bash
git clone https://github.com/vincenzo-afk/IRIS.git
cd IRIS
bash setup.sh
source venv/bin/activate
```

`setup.sh` checks for `python3`, creates `venv/` if needed, upgrades `pip`, installs `requirements.txt`, and creates `.env` from `.env.example` when it does not already exist.

Edit `.env` and add your Gemini key before starting IRIS:

```bash
$EDITOR .env
```

Then launch the interactive mode selector:

```bash
python main.py
```

The setup script also documents direct mode commands:

```bash
python main.py --mode watch
python main.py --mode chat
python main.py --mode teach
python main.py --mode voice
python main.py --mode do --task "Open Chrome and search for weather"
```

The `--mode` argument accepts `watch`, `chat`, `teach`, `do`, or `voice`. When `--mode do` is selected, `--task` supplies the natural-language goal; without it, IRIS prompts for a task interactively.

## <a name="configuration"></a>Configuration

Copying `.env.example` to `.env` provides the environment variables currently read by `config.py`:

| Variable | Required | Purpose |
|---|---:|---|
| `GEMINI_API_KEY` | Yes | Google Gemini credential used by vision, chat, agent, and local-memory model calls. |
| `MEM0_API_KEY` | No | Mem0 Cloud credential. The current default `MEMORY_LOCAL = True` means changing that code setting to `False` is also required to select the cloud path. |
| `ELEVENLABS_API_KEY` | No | Enables the ElevenLabs branch when `TTS_ENGINE` is changed from its default. |
| `IRIS_USER_ID` | No | Mem0 user namespace; defaults to `iris_user_01`. |
| `IRIS_USER_NAME` | No | Name included in assistant prompts; defaults to `User`. |

```dotenv
GEMINI_API_KEY=your_gemini_api_key_here
MEM0_API_KEY=
ELEVENLABS_API_KEY=
IRIS_USER_ID=iris_user_01
IRIS_USER_NAME=YourName
```

Additional runtime settings are constants in [`config.py`](config.py), not environment variables. They include the Gemini model names, two-second screen capture interval, JPEG quality, Whisper model name, text-to-speech engine, `hey iris` wake word, memory result count, local-memory switch, overlay appearance, 20-step maximum agent loop, and screenshot verification behavior.

### Data and secrets

`.env`, logs, screenshots, audio files, bytecode, virtual environments, build artifacts, and the local `data/` task store are excluded by [`.gitignore`](.gitignore). Never commit API keys or personal screen/audio captures. The program writes logs to `logs/iris.log` and creates screenshots and task data directories at runtime.

## <a name="usage"></a>Usage

### Watch mode

`WATCH` starts `ScreenWatcher`, periodically captures the complete desktop, sends the image to Gemini for a description, and prints a short live context line:

```bash
python main.py --mode watch
```

Press `Ctrl+C` to exit.

### Chat mode

`CHAT` reads text from the terminal, adds relevant memory and the latest screen description to the prompt, speaks each response through the configured TTS engine, and exits when you enter `quit`, `exit`, or `bye`:

```bash
python main.py --mode chat
```

### Teach mode

`TEACH` starts a topmost cursor-following Tkinter widget. After the cursor remains over an area for the configured debounce interval, IRIS captures the screen region and asks Gemini for a concise explanation:

```bash
python main.py --mode teach
```

### Autonomous task mode

`DO` starts screen awareness and the Gemini function-calling agent. The agent can perform multiple actions and stops after `MAX_AGENT_STEPS` or after calling `task_complete`:

```bash
python main.py --mode do --task "Open a terminal and type a short greeting"
```

Because this mode can control the mouse and keyboard, use narrowly scoped goals and monitor the desktop while it runs.

### Voice mode

`VOICE` starts the screen watcher, agent, overlay, and microphone listener. The listener records short utterances, transcribes them with faster-whisper, detects the configured wake word, and routes task-like commands to the autonomous agent or other commands to chat:

```bash
python main.py --mode voice
```

The default wake phrase is `hey iris`. The listener uses CPU-based Whisper inference with an `int8` compute type and records until silence or a duration limit is reached.

## <a name="agent-tools"></a>Agent Tools

IRIS exposes the following Gemini function-calling tools from `core/agent.py`:

| Tool group | Available functions |
|---|---|
| Mouse | `move_mouse`, `click`, `double_click`, `right_click`, `drag`, `scroll` |
| Keyboard and clipboard | `type_text`, `press_key`, `hotkey`, `get_clipboard` |
| Vision | `take_screenshot` |
| Applications | `open_app` |
| Web | `web_search`, `scrape_url` |
| Tasks | `add_task`, `list_tasks`, `mark_task_done` |
| Completion | `task_complete` |

The web helpers use DuckDuckGo search results and fetch page text with `requests` and BeautifulSoup. They are not an HTTP API exposed by IRIS; the repository does not contain a web server or public REST endpoints.

## <a name="project-structure"></a>Project Structure

```text
IRIS/
├── .env.example              # Environment-variable template
├── .gitignore                # Secrets and runtime-artifact exclusions
├── README.md                 # Project documentation
├── config.py                 # Models, keys, runtime settings, and paths
├── main.py                   # CLI entry point and mode orchestration
├── requirements.txt          # Python dependency specifications
├── setup.sh                  # Virtual-environment and dependency setup
├── core/
│   ├── __init__.py
│   ├── agent.py              # Gemini tool schema and autonomous loop
│   ├── automation.py         # Mouse, keyboard, clipboard, and cursor helpers
│   ├── memory.py             # Mem0 memory adapter
│   ├── vision.py             # Screen capture and Gemini vision operations
│   └── voice.py              # STT, TTS, and wake-word listener
├── overlay/
│   ├── __init__.py
│   ├── cursor_widget.py      # Cursor-following Tkinter widget
│   └── teach_mode.py         # Hover-to-explain behavior
└── tools/
    ├── __init__.py
    ├── input_tools.py        # Input helper exports
    ├── screen_tools.py       # Screen helper wrappers
    ├── system_tools.py       # App, clipboard, notification, and window helpers
    ├── task_tools.py         # JSON-backed task persistence
    └── web_tools.py          # Search and page-text extraction
```

Runtime directories such as `venv/`, `logs/`, `screenshots/`, and `data/` are created or populated locally and are intentionally not part of the source tree.

## <a name="testing"></a>Testing

No automated test suite is currently included. The repository now includes a lightweight GitHub Actions syntax check that compiles the Python source files without importing third-party packages. Run the same check locally with:

```bash
python -m compileall -q core overlay tools main.py config.py
```

This verifies Python syntax only; it does not validate API credentials, microphone access, GUI behavior, desktop permissions, model responses, or end-to-end computer-control safety.

## <a name="deployment"></a>Deployment

IRIS currently targets local desktop execution. There is no Dockerfile, container image, installer, cloud deployment manifest, or release package in the repository. The supported workflow is to create a virtual environment, install the requirements, configure `.env`, and run `main.py` on the desktop that IRIS is intended to observe or control.

A production deployment would need an explicit packaging strategy, platform-specific permission documentation, dependency locking, service/API-key isolation, a persistent memory service plan, and end-to-end tests before it should be run unattended.

## <a name="contributing"></a>Contributing

Contributions are welcome through focused pull requests. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) for the local setup, validation command, branch guidance, and pull-request expectations. Keep changes narrowly scoped, avoid committing secrets or runtime data, and document behavior changes in the README when applicable.

## <a name="security-and-privacy"></a>Security and Privacy

IRIS is a privileged desktop automation program. Depending on the mode and configuration, it can capture screen contents, record microphone input, read the clipboard, send images or text to third-party AI services, fetch web pages, and control the mouse and keyboard. Do not run it with access to sensitive sessions unless you have reviewed the code and understand the data flow.

Use environment variables for credentials, keep `.env` local, avoid unattended `DO` or `VOICE` operation on sensitive machines, and inspect the target screen before granting an action-heavy goal. Report vulnerabilities privately according to [`SECURITY.md`](SECURITY.md) rather than opening a public issue with exploit details.

## <a name="license"></a>License

No `LICENSE` file is currently present in this repository. Until the owner adds a license, the source should be treated as **all rights reserved** and should not be redistributed or reused beyond permissions granted by the copyright holder.

## <a name="acknowledgments"></a>Acknowledgments

IRIS is maintained by [vincenzo-afk](https://github.com/vincenzo-afk). The implementation builds on Google Generative AI, Mem0, Pillow, mss, pyautogui, pynput, faster-whisper, Tkinter, DuckDuckGo Search, Requests, BeautifulSoup, and related Python packages listed in [`requirements.txt`](requirements.txt).

## References

1. [Google Gemini API documentation](https://ai.google.dev/gemini-api/docs)
2. [Mem0 documentation](https://docs.mem0.ai/)
3. [Python documentation](https://docs.python.org/3/)
4. [GitHub Topics documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)

[Back to top](#iris)

---

Built by [vincenzo-afk](https://github.com/vincenzo-afk).
