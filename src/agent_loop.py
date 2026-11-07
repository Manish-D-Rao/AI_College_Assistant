"""Phase 4: agent loop with sequential + parallel tool calls (manual mode).

After executing tool(s), we append the result(s) as new message(s) and re-call the
model. The loop stops when the model returns plain text (no <tool_call>) or when
max_steps is reached. This is the "request -> execute -> respond -> repeat" cycle.

Teaching notes:
- extract_tool_calls(): returns a LIST of {name, args} for every <tool_call> block (parallel support).
- run_agent(): seeds store, loops: send -> if no tool calls, final answer; else execute all, append results, repeat.
- max_steps guard prevents infinite loops.
- Execution order matters: even "parallel" calls run in list order.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
from google import genai

import tools

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

MODEL = "gemini-3.5-flash-lite"
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

TOOL_CALLING_SYSTEM_PROMPT = """You are a helpful AI assistant with access to tools.

## Tool Usage Guidelines
- When you need to perform actions or retrieve information, choose the most appropriate tool.
- You may call multiple tools in one response if the tasks are independent.
- Provide all required parameters with accurate values.

## Tool Call Format
When you need to use a tool, output ONLY the tool call(s) in this exact format:
<tool_call>
{{"name": "tool_name", "args": {{"param1": "value1"}}}}
</tool_call>
You may repeat the <tool_call>...</tool_call> block for multiple independent calls.

## Available Tools
<tool_definitions>
{tools}
</tool_definitions>
"""


def extract_tool_calls(response_text: str) -> list[dict]:
    """Return a list of {name, args} for every <tool_call> block in the text."""
    blocks = re.findall(r"<tool_call>(.*?)</tool_call>", response_text, re.DOTALL)
    calls = []
    for b in blocks:
        obj = json.loads(b.strip())
        calls.append({"name": obj["name"], "args": obj.get("args", {})})
    return calls


def run_agent(user_prompt: str, max_steps: int = 6) -> str:
    system = TOOL_CALLING_SYSTEM_PROMPT.format(tools=str(tools.TOOLS_SCHEMA))
    messages = [system, "User: " + user_prompt]

    print("\n================ AGENT START ================")
    print("User:", user_prompt)

    for step in range(1, max_steps + 1):
        print(f"\n----- step {step} -----")
        response = client.models.generate_content(model=MODEL, contents=messages)
        text = response.text
        print("MODEL:", text.strip())

        calls = extract_tool_calls(text)
        if not calls:
            print("\n>>> FINAL ANSWER:", text.strip())
            return text.strip()

        # Execute all requested tools (parallel if multiple).
        results = []
        for c in calls:
            name, args = c["name"], c["args"]
            if name not in tools.TOOLS_BY_NAME:
                res = {"error": f"unknown tool: {name}"}
            else:
                res = tools.TOOLS_BY_NAME[name](**args)
            results.append((name, res))
            print(f"   executed {name}({args}) -> {json.dumps(res, default=str)[:200]}")

        # Feed results back to the model.
        for name, res in results:
            messages.append(f"Tool result from {name}: {json.dumps(res, default=str)}")

    print("\n>>> MAX STEPS REACHED")
    return "max steps reached"


if __name__ == "__main__":
    # Sequential example: add then list.
    run_agent("Add a task to study OS chapter 3 due 2026-11-15 medium priority, "
              "then list all pending tasks.")
