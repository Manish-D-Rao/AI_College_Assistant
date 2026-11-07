"""Phase 5: Gemini NATIVE function calling.

No manual schemas, no <tool_call> parsing. We pass the Python functions directly to
GenerateContentConfig(tools=[...]) and the SDK builds the schema from signatures /
 docstrings / type hints. We read function_call objects from the response parts.

Teaching notes:
- TOOLS: list of functions passed directly; SDK derives schema from signature/type hints/docstring.
- CONFIG: tools=TOOLS + automatic_function_calling disabled (so we control execution).
- call_tool(fc): executes the function named by fc.name with fc.args.
- run_agent(): seeds store, loops: generate -> collect function_call parts -> if none, final text; else execute all, append model turn + function_response parts, repeat.
- Good docstrings are now part of your API contract.
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

# Pass the functions directly: the SDK derives name/description/parameters from
# each function's signature, type hints and docstring.
TOOLS = [tools.add_task, tools.list_tasks, tools.mark_task_done, tools.get_task]
CONFIG = types.GenerateContentConfig(
    tools=TOOLS,
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)


def call_tool(fc) -> dict:
    """Execute a FunctionCall returned by the model."""
    name = fc.name
    args = dict(fc.args) if fc.args else {}
    if name not in tools.TOOLS_BY_NAME:
        return {"error": f"unknown tool: {name}"}
    return tools.TOOLS_BY_NAME[name](**args)


def run_agent(user_prompt: str, max_steps: int = 6) -> str:
    contents = [types.Content(role="user", parts=[types.Part(text=user_prompt)])]
    print("\n================ NATIVE AGENT START ================")
    print("User:", user_prompt)

    for step in range(1, max_steps + 1):
        print(f"\n----- step {step} -----")
        response = client.models.generate_content(model=MODEL, contents=contents, config=CONFIG)
        candidate = response.candidates[0]
        parts = candidate.content.parts or []

        # Collect function calls (if any).
        fcs = [p.function_call for p in parts if getattr(p, "function_call", None)]
        texts = [p.text for p in parts if getattr(p, "text", None)]
        if texts:
            print("MODEL TEXT:", " ".join(t for t in texts if t).strip())

        if not fcs:
            final = " ".join(t for t in texts if t).strip()
            print("\n>>> FINAL ANSWER:", final)
            return final

        # Execute all function calls.
        fr_parts = []
        for fc in fcs:
            print(f"   function_call: {fc.name}({dict(fc.args) if fc.args else {}})")
            result = call_tool(fc)
            print(f"   -> {str(result)[:200]}")
            fr_parts.append(
                types.Part(function_response=types.FunctionResponse(
                    name=fc.name, response=result))
            )

        # Append model turn + tool results, then loop.
        contents.append(candidate.content)
        contents.append(types.Content(role="user", parts=fr_parts))

    print("\n>>> MAX STEPS REACHED")
    return "max steps reached"


if __name__ == "__main__":
    run_agent("Add a task to study OS chapter 3 due 2026-11-15 medium priority, "
              "then list all pending tasks.")
