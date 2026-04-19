🤖 Project IRIS — Intelligent Real-time Interactive System
### *Full Build Plan: Autonomous AI Assistant with Vision, Voice, Cursor Overlay & Memory*

***

## 📌 Project Overview

**Goal:** Build a desktop AI agent that sees your screen, controls mouse/keyboard, speaks and listens, follows your cursor like a floating tutor, acts autonomously, and remembers everything — powered by **Gemini**  and **Mem0**. [datastudios](https://www.datastudios.org/post/google-gemini-multimodal-input-in-2025-vision-audio-and-video-capabilities-explained)

***

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────┐
│                   IRIS CORE                 │
│                                             │
│  ┌──────────┐   ┌──────────┐  ┌──────────┐ │
│  │  VISION  │   │  VOICE   │  │  MEMORY  │ │
│  │ (Gemini  │   │ STT+TTS  │  │  (Mem0)  │ │
│  │  Vision) │   │          │  │          │ │
│  └──────────┘   └──────────┘  └──────────┘ │
│                                             │
│  ┌──────────┐   ┌──────────┐  ┌──────────┐ │
│  │ CURSOR   │   │ AUTONOMY │  │AUTOMATION│ │
│  │ OVERLAY  │   │  AGENT   │  │(pyautogui│ │
│  │(Tkinter) │   │ (Gemini) │  │ /pynput) │ │
│  └──────────┘   └──────────┘  └──────────┘ │
└─────────────────────────────────────────────┘
```

***

## 📦 Module Breakdown

### Module 1 — Screen Vision
- Capture screen every 1–2 seconds using `mss` or `PIL.ImageGrab` [datastudios](https://www.datastudios.org/post/google-gemini-multimodal-input-in-2025-vision-audio-and-video-capabilities-explained)
- Send screenshot as base64 image to **Gemini 2.5 Flash** (vision model) [datastudios](https://www.datastudios.org/post/google-gemini-multimodal-input-in-2025-vision-audio-and-video-capabilities-explained)
- Gemini describes, interprets, and stores screen context
- Detects active windows, text, buttons, code, errors automatically

### Module 2 — Mouse & Keyboard Control
- `pyautogui` — mouse move, click, scroll, drag, type [youtube](https://www.youtube.com/watch?v=VSZSMAM2c9I)
- `pynput` — global keyboard/mouse listener (hotkeys, cursor tracking)
- `win32api` — low-level Windows interactions (optional for Windows users)
- All actions decided by Gemini based on current screen state + user goal

### Module 3 — Voice (Speak + Listen)
- **STT:** `faster-whisper` (local) or Google Speech API (real-time mic input) [blog](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/google-gemini-updates-io-2025/)
- **TTS:** `ElevenLabs` or `pyttsx3` for voice output
- Gemini **Live API** for real-time audio-visual conversation [cloud.google](https://cloud.google.com/blog/products/ai-machine-learning/gemini-live-api-available-on-vertex-ai)
- Wake word detection to activate listening mode

### Module 4 — Cursor Overlay (Tutor Widget)
- `tkinter` floating window: `overrideredirect(True)` + `attributes('-topmost', True)` [reddit](https://www.reddit.com/r/Python/comments/op1tz0/tkinter_was_shockingly_easy_to_write_a_small/)
- Tracks real cursor via `pynput.mouse.Listener` — overlay follows cursor position
- In **TEACH MODE**: overlay pops explanations next to whatever the cursor hovers over
- Transparent background with rounded UI using `wm_attributes('-transparentcolor', ...)`

### Module 5 — Autonomous Agent Brain
- Gemini 2.5 Pro as the reasoning engine [datastudios](https://www.datastudios.org/post/google-gemini-multimodal-input-in-2025-vision-audio-and-video-capabilities-explained)
- Agent loop: `observe → think → plan → act → verify → repeat`
- Uses **Gemini 2.5 Computer Use** model for computer interaction tasks [storage.googleapis](https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-2-5-Computer-Use-Model-Card.pdf)
- Tool-calling: each action (click, type, scroll, screenshot) is a callable tool

### Module 6 — Persistent Memory (Mem0)
- `pip install mem0ai` [mem0](https://mem0.ai)
- Store: user preferences, past tasks, project context, teaching history
- Retrieve: relevant memories injected into every Gemini prompt [docs.mem0](https://docs.mem0.ai/cookbooks/integrations/agents-sdk-tool)
- Auto-update memory after every session ends [mem0](https://mem0.ai)

***

## 🗂️ File Structure

```
IRIS/
│
├── main.py                  # Entry point, mode selector
├── config.py                # API keys, user_id, settings
│
├── core/
│   ├── vision.py            # Screen capture + Gemini Vision
│   ├── voice.py             # STT + TTS pipeline
│   ├── agent.py             # Autonomous agent brain (Gemini)
│   ├── memory.py            # Mem0 read/write/search
│   └── automation.py        # pyautogui + pynput actions
│
├── overlay/
│   ├── cursor_widget.py     # Floating tkinter overlay
│   └── teach_mode.py        # Cursor-follow teach annotations
│
├── tools/
│   ├── screen_tools.py      # screenshot, find_element, read_text
│   ├── input_tools.py       # click, type, scroll, hotkey
│   └── system_tools.py      # open_app, get_clipboard, notify
│
└── requirements.txt
```

***

## 🔄 Operational Modes

| Mode | Trigger | Behavior |
|---|---|---|
| **WATCH** | On startup | Silent screen reading, builds context |
| **TEACH** | `"Hey IRIS, explain this"` | Cursor overlay active, narrates UI elements |
| **DO** | `"Hey IRIS, do X for me"` | Full autonomous task execution |
| **CHAT** | Wake word / hotkey | Voice or text conversation mode |
| **LEARN** | After each session | Mem0 memory update, self-improvement |

***

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| LLM + Vision | Gemini 2.5 Flash / Pro  [datastudios](https://www.datastudios.org/post/google-gemini-multimodal-input-in-2025-vision-audio-and-video-capabilities-explained) |
| Computer Use | Gemini 2.5 Computer Use  [storage.googleapis](https://storage.googleapis.com/deepmind-media/Model-Cards/Gemini-2-5-Computer-Use-Model-Card.pdf) |
| Real-time Voice | Gemini Live API  [cloud.google](https://cloud.google.com/blog/products/ai-machine-learning/gemini-live-api-available-on-vertex-ai) |
| Memory | Mem0 (`mem0ai`)  [mem0](https://mem0.ai) |
| Screen Capture | `mss`, `PIL` |
| Automation | `pyautogui`, `pynput`, `win32api` |
| Overlay UI | `tkinter` or `PyQt5`  [reddit](https://www.reddit.com/r/Python/comments/op1tz0/tkinter_was_shockingly_easy_to_write_a_small/) |
| STT | `faster-whisper`, Google Speech |
| TTS | `ElevenLabs`, `pyttsx3`, `gTTS` |

***

## 📋 Build Phases

**Phase 1 — Foundation (Week 1)**
- Set up Gemini API + Mem0 SDK
- Basic screen capture → Gemini Vision → text description
- Voice input (Whisper STT) + voice output (TTS) working

**Phase 2 — Automation (Week 2)**
- pyautogui mouse/keyboard control
- Gemini deciding actions from screen context
- Basic agent loop: goal → steps → execute

**Phase 3 — Overlay (Week 3)**
- Floating tkinter cursor widget
- Real-time cursor tracking with pynput
- Teach mode: hover detection + Gemini explanation callout

**Phase 4 — Autonomy + Memory (Week 4)**
- Full agent brain with tool-calling
- Mem0 memory injection into every prompt
- Session persistence and preference learning

**Phase 5 — Polish (Week 5)**
- Mode switcher UI
- Error recovery and self-correction loops
- Packaging with PyInstaller or Docker

***

## 📦 Requirements

```txt
google-generativeai
mem0ai
pyautogui
pynput
mss
Pillow
faster-whisper
elevenlabs
pyttsx3
pywin32
tkinter
opencv-python
sounddevice
numpy
python-dotenv
```