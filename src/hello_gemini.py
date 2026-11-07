"""Phase 0 smoke test: load env and ask Gemini one question.

Teaching notes:
- os / pathlib: locate the project root so .env is found regardless of cwd.
- dotenv.load_dotenv: reads KEY=VALUE pairs from .env into os.environ (secrets stay out of code).
- genai.Client(api_key=...): creates an authenticated client for the Gemini API.
- client.models.generate_content(...): sends a single prompt, returns a response object.
- response.text: the model's plain-text reply (no tool calling here).
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# Resolve project root = parent of this file's directory (src/ -> project root).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Load secrets from .env (never commit .env; see .gitignore).
load_dotenv(PROJECT_ROOT / ".env")

# Read the API key from the environment (injected by load_dotenv above).
api_key = os.getenv("GEMINI_API_KEY")
# Guard: fail early with a helpful message instead of a cryptic API error.
if not api_key or api_key == "your_api_key_here":
    raise SystemExit(
        "GEMINI_API_KEY is not set. Edit .env and paste your key from "
        "https://aistudio.google.com/apikey"
    )

# Authenticated client. Passing api_key explicitly is clearer than relying on env.
client = genai.Client(api_key=api_key)

# Model id. Keep this in one place so it is easy to swap.
MODEL = "gemini-3.5-flash-lite"

# Single, non-streaming request. `contents` can be a string or a list of parts.
response = client.models.generate_content(
    model=MODEL,
    contents="In one sentence, what is tool calling in AI agents?",
)

# Print the model id and its reply.
print("Model:", MODEL)
print("Reply:", response.text)
