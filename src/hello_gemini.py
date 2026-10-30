"""Phase 0 smoke test: load env and ask Gemini one question."""

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# Load .env from project root (parent of this file's directory).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your_api_key_here":
    raise SystemExit(
        "GEMINI_API_KEY is not set. Edit .env and paste your key from "
        "https://aistudio.google.com/apikey"
    )

# Create the Gemini client. With google-genai, passing api_key explicitly is clearest.
client = genai.Client(api_key=api_key)

MODEL = "gemini-3.5-flash-lite"

response = client.models.generate_content(
    model=MODEL,
    contents="In one sentence, what is tool calling in AI agents?",
)

print("Model:", MODEL)
print("Reply:", response.text)
