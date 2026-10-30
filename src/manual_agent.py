"""Phase 3: tool selection by LLM in MANUAL mode.

We hand-write the system prompt (with TOOLS_SCHEMA) and ask Gemini to emit a
<tool_call>{...}</tool_call> block. We then parse that block and execute the tool.
This mirrors the article's "Implementing Tool Calls From Scratch" section.
In Phase 5 we drop all of this in favour of Gemini's native function calling.
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


# ---------------------------------------------------------------------------
# System prompt: guidelines + <tool_call> format + available tool schemas
# ---------------------------------------------------------------------------
TOOL_CALLING_SYSTEM_PROMPT = """You are a helpful AI assistant with access to tools.

## Tool Usage Guidelines
- When you need to perform actions or retrieve information, choose the most appropriate tool.
- Choose different tools based on their descriptions.
- Provide all required parameters with accurate values.

## Tool Call Format
When you need to use a tool, output ONLY the tool call in this exact format:
<tool_call>
{{"name": "tool_name", "args": {{"param1": "value1"}}}}
</tool_call>

## Available Tools
<tool_definitions>
{tools}
</tool_definitions>
"""


def build_prompt(user_prompt: str) -> str:
    return TOOL_CALLING_SYSTEM_PROMPT.format(tools=str(tools.TOOLS_SCHEMA)) + "\n\nUser: " + user_prompt


def extract_tool_call(response_text: str) -> str:
    """Extract the JSON string inside <tool_call> ... </tool_call>."""
    match = re.search(r"<tool_call>(.*?)</tool_call>", response_text, re.DOTALL)
    if not match:
        raise ValueError("No <tool_call> block found in model response")
    return match.group(1).strip()


def call_tool(response_text: str, tools_by_name: dict) -> dict:
    """Parse the LLM response and execute the requested tool."""
    tool_call_str = extract_tool_call(response_text)
    tool_call = json.loads(tool_call_str)
    tool_name = tool_call["name"]
    tool_args = tool_call.get("args", {})
    if tool_name not in tools_by_name:
        return {"error": f"unknown tool: {tool_name}"}
    handler = tools_by_name[tool_name]
    return handler(**tool_args)


def run_once(user_prompt: str) -> None:
    print("\n=== USER ===")
    print(user_prompt)
    prompt = build_prompt(user_prompt)
    response = client.models.generate_content(model=MODEL, contents=prompt)
    text = response.text
    print("\n=== MODEL RAW RESPONSE ===")
    print(text)
    try:
        result = call_tool(text, tools.TOOLS_BY_NAME)
        print("\n=== TOOL RESULT ===")
        print(json.dumps(result, indent=2, default=str))
    except (ValueError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"\n=== PARSE/EXEC ERROR: {exc} ===")


if __name__ == "__main__":
    tools._reset_store()
    tools.add_task("Study DBMS Ch5", "DBMS", "2026-11-10", "high")
    tools.add_task("OS lab report", "OS", "2026-11-12")

    run_once("List all my pending study tasks.")
    run_once("Add a task to study OS chapter 3, due 2026-11-15, medium priority.")
