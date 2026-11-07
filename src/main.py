"""Phase 8 — CLI REPL for AI College Assistant.

A simple command-line REPL that lets you interact with the assistant
using Gemini's native function calling. Type `quit` or `exit` to stop.

Usage hints:
  - Natural language prompts work best
  - Supported actions: add tasks, list tasks, mark done, get task
  - Dates in YYYY-MM-DD format
  - Tasks persist across prompts (database persists in data/tasks.db)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from google import genai
from google.genai import types

import tools

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MODEL = "gemini-3.5-flash-lite"
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

TOOLS = [tools.add_task, tools.list_tasks, tools.mark_task_done, tools.get_task]
CONFIG = types.GenerateContentConfig(
    tools=TOOLS,
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)


def call_tool(fc) -> dict:
    name = fc.name
    args = dict(fc.args) if fc.args else {}
    if name not in tools.TOOLS_BY_NAME:
        return {"error": f"unknown tool: {name}"}
    return tools.TOOLS_BY_NAME[name](**args)


def run_cycle(user_prompt: str) -> str:
    """Run one prompt through the native agent loop and return the final text."""
    contents = [types.Content(role="user", parts=[types.Part(text=user_prompt)])]

    for step in range(1, 7):
        response = client.models.generate_content(model=MODEL, contents=contents, config=CONFIG)
        candidate = response.candidates[0]
        parts = candidate.content.parts or []

        fcs = [p.function_call for p in parts if getattr(p, "function_call", None)]
        texts = [p.text for p in parts if getattr(p, "text", None)]

        if not fcs:
            final = " ".join(t for t in texts if t).strip()
            return final

        fr_parts = []
        for fc in fcs:
            result = call_tool(fc)
            fr_parts.append(types.Part(function_response=types.FunctionResponse(name=fc.name, response=result)))

        contents.append(candidate.content)
        contents.append(types.Content(role="user", parts=fr_parts))

    return "max steps reached"


def main():
    banner = ("\n=== AI College Assistant ==="
              "\nYour personal study-task assistant powered by Gemini tool calling.\n")
    print(banner)
    print("Supported prompts (examples):")
    print("  • List my pending tasks")
    print("  • Add a task to study DBMS Chapter 6 due 2026-12-01 high priority")
    print("  • Mark task 1 as done")
    print("  • What do I have due this week?")
    print("\nType 'quit' or 'exit' to stop.\n")

    while True:
        try:
            prompt = input("\nPrompt: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not prompt:
            continue
        if prompt.lower() in {"quit", "exit"}:
            print("Goodbye!")
            break

        print("\nThinking...")
        final = run_cycle(prompt)
        print("\n" + "=" * 40)
        print(final)
        print("=" * 40)


if __name__ == "__main__":
    main()
