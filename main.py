"""
╔══════════════════════════════════════════════════════════╗
║           IRIS — Intelligent Real-time Interactive System ║
║                     Entry Point                          ║
╚══════════════════════════════════════════════════════════╝

Usage:
    python main.py                  → Interactive mode selector
    python main.py --mode watch     → Silent screen-watching
    python main.py --mode chat      → Conversational mode
    python main.py --mode teach     → Cursor-overlay teach mode
    python main.py --mode do        → Give a one-shot autonomous task
    python main.py --mode voice     → Voice-only interaction
"""

import argparse
import logging
import sys
import threading
import time
from typing import Optional

# ── Logging setup ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/iris.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("IRIS")


class IRIS:
    """
    Top-level orchestrator.
    Initializes all modules and routes between operational modes.
    """

    def __init__(self):
        self.mode: str = "chat"
        self.screen_watcher = None
        self.voice_listener = None
        self.cursor_widget = None
        self.teach_mode = None
        self.agent = None
        self._shutdown_event = threading.Event()

    # ── Initialization ──────────────────────────────────────────

    def _init_screen_watcher(self):
        from core.vision import ScreenWatcher
        self.screen_watcher = ScreenWatcher(
            on_update=lambda desc, img: logger.debug("Screen: %s…", desc[:60])
        )
        self.screen_watcher.start()
        logger.info("Screen watcher online")

    def _init_overlay(self):
        from overlay.cursor_widget import CursorWidget
        self.cursor_widget = CursorWidget()
        self.cursor_widget.start()
        logger.info("Cursor overlay online")

    def _init_teach(self):
        if self.cursor_widget is None:
            self._init_overlay()
        from overlay.teach_mode import TeachMode
        self.teach_mode = TeachMode(self.cursor_widget)
        self.teach_mode.start()
        logger.info("Teach mode online")

    def _init_agent(self):
        from core.agent import IRISAgent
        self.agent = IRISAgent(screen_watcher=self.screen_watcher)
        logger.info("Agent brain online")

    def _init_voice(self, on_command):
        from core.voice import VoiceListener
        self.voice_listener = VoiceListener(on_command=on_command)
        self.voice_listener.start()
        logger.info("Voice listener online")

    # ── Modes ───────────────────────────────────────────────────

    def run_watch_mode(self):
        """Silently watch the screen. CTRL+C to exit."""
        logger.info("=== IRIS: WATCH MODE ===")
        self._init_screen_watcher()

        print("\n[IRIS] WATCH MODE active. Monitoring your screen silently.")
        print("[IRIS] Press CTRL+C to exit.\n")

        try:
            while not self._shutdown_event.is_set():
                if self.screen_watcher:
                    ctx = self.screen_watcher.get_context()
                    print(f"\r[SCREEN] {ctx[:100]:<100}", end="", flush=True)
                time.sleep(5)
        except KeyboardInterrupt:
            pass

    def run_chat_mode(self):
        """Text-based conversational chat with memory and screen awareness."""
        from core.agent import chat
        from core.voice import speak

        logger.info("=== IRIS: CHAT MODE ===")
        self._init_screen_watcher()

        print("\n╔════════════════════════════════╗")
        print("║     IRIS — CHAT MODE           ║")
        print("║  Type your message or 'quit'   ║")
        print("╚════════════════════════════════╝\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                break

            if user_input.lower() in ("quit", "exit", "bye"):
                speak("Goodbye!")
                break

            if not user_input:
                continue

            screen_ctx = ""
            if self.screen_watcher:
                screen_ctx = self.screen_watcher.latest_description

            response = chat(user_input, screen_context=screen_ctx)
            print(f"\nIRIS: {response}\n")
            speak(response)

    def run_teach_mode(self):
        """Overlay explains whatever the cursor hovers over."""
        from core.voice import speak

        logger.info("=== IRIS: TEACH MODE ===")
        self._init_overlay()
        self._init_teach()

        print("\n[IRIS] TEACH MODE active.")
        print("[IRIS] Hover your cursor over any UI element to get an explanation.")
        print("[IRIS] Press CTRL+C to exit.\n")
        speak("Teach mode activated. Hover over anything and I'll explain it.")

        try:
            self._shutdown_event.wait()
        except KeyboardInterrupt:
            pass

    def run_do_mode(self, goal: Optional[str] = None):
        """Autonomous task execution mode."""
        from core.voice import speak

        logger.info("=== IRIS: DO MODE ===")
        self._init_screen_watcher()
        self._init_agent()

        if not goal:
            print("\n[IRIS] DO MODE — What should I do for you?")
            goal = input("Task: ").strip()

        if not goal:
            print("[IRIS] No task given. Exiting.")
            return

        speak(f"Got it. I'll {goal} for you now.")
        print(f"\n[IRIS] Executing: {goal}\n")

        def on_step(step, tool, result):
            print(f"  Step {step}: {tool}() → {result[:80]}")

        result = self.agent.run(goal, on_step=on_step)
        print(f"\n[IRIS] Done: {result}\n")
        speak(f"Task complete. {result}")

    def run_voice_mode(self):
        """Wake-word driven voice interaction."""
        from core.voice import speak

        logger.info("=== IRIS: VOICE MODE ===")
        self._init_screen_watcher()
        self._init_agent()
        self._init_overlay()

        speak("IRIS voice mode activated. Say 'Hey IRIS' followed by your command.")
        print("\n[IRIS] VOICE MODE — Listening for 'Hey IRIS...'")

        def on_command(text: str):
            from core.agent import chat

            print(f"\n[IRIS] Heard: {text}")
            if self.cursor_widget:
                self.cursor_widget.show_message(f"🎤 {text}")

            # Route: autonomous task vs conversational reply
            task_keywords = ("open ", "click ", "go to", "type ", "search ", "download ", "write ")
            is_task = any(text.lower().startswith(kw) for kw in task_keywords)

            if is_task and self.agent:
                speak("On it.")
                result = self.agent.run(text)
                speak(result)
            else:
                screen_ctx = self.screen_watcher.latest_description if self.screen_watcher else ""
                response = chat(text, screen_context=screen_ctx)
                speak(response)
                if self.cursor_widget:
                    self.cursor_widget.show_message(f"💬 {response[:120]}")

        self._init_voice(on_command)

        try:
            while not self._shutdown_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    # ── Shutdown ────────────────────────────────────────────────

    def shutdown(self):
        logger.info("Shutting down IRIS…")
        self._shutdown_event.set()
        if self.screen_watcher:
            self.screen_watcher.stop()
        if self.voice_listener:
            self.voice_listener.stop()
        if self.teach_mode:
            self.teach_mode.stop()
        if self.cursor_widget:
            self.cursor_widget.stop()
        logger.info("IRIS offline.")


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────

BANNER = r"""
 ██╗██████╗ ██╗███████╗
 ██║██╔══██╗██║██╔════╝
 ██║██████╔╝██║███████╗
 ██║██╔══██╗██║╚════██║
 ██║██║  ██║██║███████║
 ╚═╝╚═╝  ╚═╝╚═╝╚══════╝
 Intelligent Real-time Interactive System
"""


def main():
    parser = argparse.ArgumentParser(
        description="IRIS — AI Desktop Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode",
        choices=["watch", "chat", "teach", "do", "voice"],
        default=None,
        help="Operational mode to start in",
    )
    parser.add_argument(
        "--task",
        type=str,
        default=None,
        help="Task description for --mode do",
    )
    args = parser.parse_args()

    print(BANNER)

    iris = IRIS()

    # Interactive mode selector if not specified
    if args.mode is None:
        print("Select mode:")
        print("  1) watch  — Silent screen monitoring")
        print("  2) chat   — Text conversation")
        print("  3) teach  — Cursor explanations")
        print("  4) do     — Autonomous task")
        print("  5) voice  — Voice commands")
        choice = input("\nChoice [1-5]: ").strip()
        mode_map = {"1": "watch", "2": "chat", "3": "teach", "4": "do", "5": "voice"}
        args.mode = mode_map.get(choice, "chat")

    try:
        if args.mode == "watch":
            iris.run_watch_mode()
        elif args.mode == "chat":
            iris.run_chat_mode()
        elif args.mode == "teach":
            iris.run_teach_mode()
        elif args.mode == "do":
            iris.run_do_mode(goal=args.task)
        elif args.mode == "voice":
            iris.run_voice_mode()
    finally:
        iris.shutdown()


if __name__ == "__main__":
    main()
