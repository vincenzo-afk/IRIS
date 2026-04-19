"""
IRIS Configuration File
=======================
Central hub for all API keys, model settings, and system-wide configuration.
Copy this file and fill in your actual keys before running.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# API KEYS
# ──────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
MEM0_API_KEY: str = os.getenv("MEM0_API_KEY", "")          # leave blank for local Mem0
ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")

# ──────────────────────────────────────────────
# MODEL SELECTION
# ──────────────────────────────────────────────
GEMINI_VISION_MODEL: str = "gemini-2.0-flash"              # Screen vision + fast tasks
GEMINI_PRO_MODEL: str = "gemini-2.5-pro-preview-03-25"    # Deep reasoning / agent brain
GEMINI_LIVE_MODEL: str = "gemini-2.0-flash-live-001"      # Real-time voice

# ──────────────────────────────────────────────
# USER IDENTITY
# ──────────────────────────────────────────────
USER_ID: str = os.getenv("IRIS_USER_ID", "iris_user_01")   # Mem0 user namespace
USER_NAME: str = os.getenv("IRIS_USER_NAME", "User")

# ──────────────────────────────────────────────
# SCREEN CAPTURE
# ──────────────────────────────────────────────
CAPTURE_INTERVAL: float = 2.0          # Seconds between screen captures
CAPTURE_QUALITY: int = 85              # JPEG quality (1-100) for base64 encoding
CAPTURE_MAX_WIDTH: int = 1920          # Resize if wider than this
CAPTURE_MAX_HEIGHT: int = 1080

# ──────────────────────────────────────────────
# VOICE SETTINGS
# ──────────────────────────────────────────────
STT_MODEL: str = "base"                # Whisper model: tiny / base / small / medium / large
TTS_ENGINE: str = "pyttsx3"            # "pyttsx3" | "elevenlabs" | "gtts"
ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"   # Rachel voice
TTS_RATE: int = 170                    # pyttsx3 speech rate (words/min)
WAKE_WORD: str = "hey iris"            # Lowercase wake word phrase

# ──────────────────────────────────────────────
# MEMORY (Mem0)
# ──────────────────────────────────────────────
MEMORY_TOP_K: int = 5                  # Number of memories to inject per prompt
MEMORY_LOCAL: bool = True              # True = use local Qdrant, False = Mem0 cloud

# ──────────────────────────────────────────────
# OVERLAY / UI
# ──────────────────────────────────────────────
OVERLAY_WIDTH: int = 360
OVERLAY_HEIGHT: int = 80
OVERLAY_OFFSET_X: int = 20             # X offset from cursor
OVERLAY_OFFSET_Y: int = 20
OVERLAY_BG: str = "#0d0d0d"
OVERLAY_FG: str = "#00ff88"
OVERLAY_FONT: tuple = ("Segoe UI", 11)
OVERLAY_ALPHA: float = 0.92            # Window transparency (0-1)

# ──────────────────────────────────────────────
# AGENT
# ──────────────────────────────────────────────
MAX_AGENT_STEPS: int = 20              # Safety: max tool calls per goal
AGENT_STEP_DELAY: float = 0.5         # Seconds between agent actions
SCREENSHOT_ON_VERIFY: bool = True      # Take screenshot after every action

# ──────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
