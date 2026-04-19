"""
IRIS — Autonomous Agent Brain
================================
Implements the observe → think → plan → act → verify → repeat loop.
Uses Gemini 2.5 Pro with tool-calling to decide which action to take.
Memory context is injected into every prompt.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

import google.generativeai as genai

from config import (
    GEMINI_API_KEY,
    GEMINI_PRO_MODEL,
    MAX_AGENT_STEPS,
    AGENT_STEP_DELAY,
    SCREENSHOT_ON_VERIFY,
    USER_NAME,
)
from core import memory as mem
from core import automation as auto
from core.vision import analyze_screen, capture_screenshot

logger = logging.getLogger(__name__)
genai.configure(api_key=GEMINI_API_KEY)


# ──────────────────────────────────────────────────────────────
# TOOL DEFINITIONS (Gemini function-calling schema)
# ──────────────────────────────────────────────────────────────

TOOLS = [
    genai.protos.Tool(
        function_declarations=[
            genai.protos.FunctionDeclaration(
                name="double_click",
                description="Double-click the mouse at the given screen coordinates.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "x": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="X pixel coordinate"),
                        "y": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="Y pixel coordinate"),
                    },
                    required=["x", "y"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="right_click",
                description="Right-click the mouse at the given screen coordinates.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "x": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="X pixel coordinate"),
                        "y": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="Y pixel coordinate"),
                    },
                    required=["x", "y"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="drag",
                description="Drag the mouse from one point to another.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "x1": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="Start X pixel coordinate"),
                        "y1": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="Start Y pixel coordinate"),
                        "x2": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="End X pixel coordinate"),
                        "y2": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="End Y pixel coordinate"),
                    },
                    required=["x1", "y1", "x2", "y2"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="move_mouse",
                description="Move the mouse to the given screen coordinates without clicking.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "x": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="X pixel coordinate"),
                        "y": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="Y pixel coordinate"),
                    },
                    required=["x", "y"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="click",
                description="Click the mouse at the given screen coordinates.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "x": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="X pixel coordinate"),
                        "y": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="Y pixel coordinate"),
                        "button": genai.protos.Schema(type=genai.protos.Type.STRING, description="'left' or 'right'"),
                    },
                    required=["x", "y"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="type_text",
                description="Type text into the currently focused input field.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "text": genai.protos.Schema(type=genai.protos.Type.STRING, description="Text to type"),
                    },
                    required=["text"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="press_key",
                description="Press a keyboard key by name (enter, tab, escape, f5, etc.).",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "key": genai.protos.Schema(type=genai.protos.Type.STRING, description="Key name"),
                    },
                    required=["key"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="hotkey",
                description="Press a keyboard shortcut like ctrl+c, ctrl+v, alt+tab.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "keys": genai.protos.Schema(type=genai.protos.Type.STRING, description="Keys joined by '+', e.g. 'ctrl+c'"),
                    },
                    required=["keys"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="scroll",
                description="Scroll the mouse wheel at the given coordinates.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "x": genai.protos.Schema(type=genai.protos.Type.INTEGER),
                        "y": genai.protos.Schema(type=genai.protos.Type.INTEGER),
                        "clicks": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="Number of scroll clicks (default 3)"),
                        "direction": genai.protos.Schema(type=genai.protos.Type.STRING, description="'up' or 'down'"),
                    },
                    required=["x", "y"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="take_screenshot",
                description="Capture the current screen and get a description of what is visible.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={},
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="open_app",
                description="Open an application by name (e.g. 'chrome', 'notepad', 'terminal').",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "app_name": genai.protos.Schema(type=genai.protos.Type.STRING),
                    },
                    required=["app_name"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="get_clipboard",
                description="Read the content currently in the clipboard.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={},
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="web_search",
                description="Search the web for real-time information.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "query": genai.protos.Schema(type=genai.protos.Type.STRING, description="Search query"),
                    },
                    required=["query"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="scrape_url",
                description="Scrape and extract text content from a url.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "url": genai.protos.Schema(type=genai.protos.Type.STRING),
                    },
                    required=["url"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="task_complete",
                description="Signal that the task has been completed successfully. Call this as the final action.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "summary": genai.protos.Schema(type=genai.protos.Type.STRING, description="Brief description of what was accomplished"),
                    },
                    required=["summary"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="add_task",
                description="Schedule or add a new task to the user's workflow.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "title": genai.protos.Schema(type=genai.protos.Type.STRING),
                        "description": genai.protos.Schema(type=genai.protos.Type.STRING),
                        "scheduled_time": genai.protos.Schema(type=genai.protos.Type.STRING),
                    },
                    required=["title"],
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="list_tasks",
                description="List all pending scheduled tasks and workflows.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={},
                ),
            ),
            genai.protos.FunctionDeclaration(
                name="mark_task_done",
                description="Mark a workflow task as completed by ID or name.",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "task_id": genai.protos.Schema(type=genai.protos.Type.STRING),
                    },
                    required=["task_id"],
                ),
            ),

def execute_tool(name: str, args: Dict[str, Any]) -> str:
    """Dispatch a tool call to the automation layer and return result."""
    logger.info("Tool: %s(%s)", name, args)

    try:
        if name == "click":
            auto.click(args.get("x"), args.get("y"), args.get("button", "left"))
            return "Clicked successfully"

        elif name == "double_click":
            auto.double_click(args["x"], args["y"])
            return f"Double-clicked at ({args['x']}, {args['y']})"

        elif name == "right_click":
            auto.right_click(args["x"], args["y"])
            return f"Right-clicked at ({args['x']}, {args['y']})"

        elif name == "drag":
            auto.drag(args["x1"], args["y1"], args["x2"], args["y2"])
            return f"Dragged from ({args['x1']}, {args['y1']}) to ({args['x2']}, {args['y2']})"

        elif name == "move_mouse":
            auto.move_mouse(args["x"], args["y"])
            return f"Moved mouse to ({args['x']}, {args['y']})"

        elif name == "type_text":
            auto.type_text_raw(args["text"])
            return "Text typed"

        elif name == "press_key":
            auto.press_key(args["key"])
            return f"Key '{args['key']}' pressed"

        elif name == "hotkey":
            keys = args["keys"].split("+")
            auto.hotkey(*keys)
            return f"Hotkey {args['keys']} pressed"

        elif name == "scroll":
            auto.scroll(
                x=args.get("x", 0),
                y=args.get("y", 0),
                clicks=args.get("clicks", 3),
                direction=args.get("direction", "down"),
            )
            return "Scrolled"

        elif name == "take_screenshot":
            img = capture_screenshot()
            desc = analyze_screen(img)
            return f"Screen state: {desc}"

        elif name == "open_app":
            from tools.system_tools import open_app
            return open_app(args["app_name"])

        elif name == "get_clipboard":
            content = auto.get_clipboard()
            return f"Clipboard: {content[:500]}"

        elif name == "web_search":
            from tools.web_tools import web_search
            return web_search(args["query"])

        elif name == "scrape_url":
            from tools.web_tools import scrape_url
            return scrape_url(args["url"])

        elif name == "task_complete":
            return f"DONE: {args.get('summary', '')}"

        elif name == "add_task":
            from tools.task_tools import add_task
            return add_task(args["title"], args.get("description", ""), args.get("scheduled_time", ""))

        elif name == "list_tasks":
            from tools.task_tools import list_tasks
            return list_tasks()

        elif name == "mark_task_done":
            from tools.task_tools import mark_task_done
            return mark_task_done(args["task_id"])

        else:
            return f"Unknown tool: {name}"

    except Exception as exc:
        logger.error("Tool %s error: %s", name, exc)
        return f"Error executing {name}: {exc}"


# ──────────────────────────────────────────────────────────────
# AGENT LOOP
# ──────────────────────────────────────────────────────────────

class IRISAgent:
    """The autonomous reasoning loop for IRIS."""

    def __init__(self, screen_watcher=None):
        self.screen_watcher = screen_watcher
        self._model = genai.GenerativeModel(
            model_name=GEMINI_PRO_MODEL,
            tools=TOOLS,
        )

    def _build_system_prompt(self, goal: str, screen_context: str, memory_context: str) -> str:
        from tools.task_tools import list_tasks
        tasks_ctx = list_tasks()
        return f"""You are IRIS, an autonomous AI desktop agent and daily personal assistant.

User name: {USER_NAME}
Current goal: {goal}

[Current Workflows / Pending Tasks (What the user left half done)]
{tasks_ctx}

{memory_context}

Current screen state:
{screen_context}

Your job is to accomplish the goal by calling the available tools in sequence.
Think step by step. If the user greets you (e.g. "I'm here" or "I'm home"), ALWAYS greet them back, read the pending tasks, report what they left half-done, ask what they'd like to tackle, and then open their daily work environment if they agree. 
Manage schedules actively: add, list, or complete tasks as instructed. You have full computer control.
CRITICAL INSTRUCTION: You are highly intelligent, multimodal, and multilingual. You MUST converse and respond with intelligence and insight in the exact language the user uses.
If the user asks "what is this" or "what happened", use the screen context to identify exactly what they are referring to or use web search to verify what it is before explaining. Ask intelligent clarifying questions when appropriate. Utilize web search to gather real-time data when needed!
"""

    def run(self, goal: str, on_step: Optional[Any] = None) -> str:
        """
        Execute the observe→think→plan→act→verify loop.

        Args:
            goal: Natural language task to accomplish.
            on_step: Optional callback(step_num, tool_name, result) for progress updates.

        Returns:
            Final summary string.
        """
        logger.info("=== Agent START: %s ===", goal)

        # 1. Observe
        screen_ctx = (
            self.screen_watcher.get_context()
            if self.screen_watcher
            else analyze_screen()
        )

        # 2. Inject memory
        mem_ctx = mem.build_memory_context(goal)

        # 3. Build initial prompt
        system_prompt = self._build_system_prompt(goal, screen_ctx, mem_ctx)

        chat = self._model.start_chat()
        response = chat.send_message(system_prompt)

        final_summary = ""
        steps = 0

        while steps < MAX_AGENT_STEPS:
            # Check for tool calls
            tool_calls = [
                part.function_call
                for part in response.candidates[0].content.parts
                if hasattr(part, "function_call") and part.function_call.name
            ]

            if not tool_calls:
                # Model responded with text — treat as final answer
                texts = [
                    part.text
                    for part in response.candidates[0].content.parts
                    if hasattr(part, "text")
                ]
                final_summary = " ".join(texts)
                break

            # Execute tools
            tool_results = []
            for fc in tool_calls:
                name = fc.name
                args = dict(fc.args)
                result = execute_tool(name, args)

                if on_step:
                    on_step(steps + 1, name, result)

                tool_results.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=name,
                            response={"result": result},
                        )
                    )
                )

                if name == "task_complete":
                    final_summary = result
                    logger.info("=== Agent DONE in %d steps ===", steps + 1)
                    mem.save_session_summary(f"Goal: {goal}\nResult: {final_summary}")
                    return final_summary

            # Verify (optional new screenshot)
            if SCREENSHOT_ON_VERIFY:
                time.sleep(AGENT_STEP_DELAY)
                img = capture_screenshot()
                new_ctx = analyze_screen(img)
                # append screen context to tool response
                tool_results.append(
                    genai.protos.Part(text=f"[Updated screen] {new_ctx}")
                )

            response = chat.send_message(tool_results)
            steps += 1

        logger.info("=== Agent STOPPED after %d steps ===", steps)
        if not final_summary:
            final_summary = f"Reached step limit ({MAX_AGENT_STEPS}) before completing goal."

        mem.save_session_summary(f"Goal: {goal}\nResult: {final_summary}")
        return final_summary


# ──────────────────────────────────────────────────────────────
# SIMPLE CHAT (non-autonomous)
# ──────────────────────────────────────────────────────────────

_chat_model = genai.GenerativeModel(GEMINI_PRO_MODEL)
_chat_session = None


def chat(message: str, screen_context: str = "") -> str:
    """
    Single-turn conversational response (CHAT mode).
    Memory is injected; no tool-calling involved.
    """
    global _chat_session

    mem_ctx = mem.build_memory_context(message)

    if _chat_session is None:
        system = (
            f"You are IRIS, a highly intelligent daily personal assistant for {USER_NAME}. "
            "You can see the screen, control the computer, and remember past sessions. "
            "CRITICAL: Be extremely proactive. If the user says 'I'm here' or 'I'm home', greet them, review their pending tasks/records, report what they left in half, and act as a dedicated PA keeping everything scheduled. You must provide real-time search, answer questions intelligently, ask relevant questions to the user, and explain visual items on the screen when the user asks 'what is this' or 'what happened'. Strictly speak the user's exact language."
        )
        _chat_session = _chat_model.start_chat()
        _chat_session.send_message(system)

    prompt = message
    if mem_ctx:
        prompt = f"{mem_ctx}\n\n{message}"
    if screen_context:
        prompt += f"\n\n[Current screen] {screen_context}"

    response = _chat_session.send_message(prompt)
    reply = response.text.strip()

    # Save conversation to memory
    mem.add_memory(f"User asked: {message}\nIRIS replied: {reply[:200]}")
    return reply
