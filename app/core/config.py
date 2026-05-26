from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

OPENAI_KEY = os.getenv("OPENAI_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL") if os.getenv("OPENAI_MODEL") else "gpt-5.4-mini"
MAX_LLM_INPUT_CHARS = int(os.getenv("MAX_LLM_INPUT_CHARS", "15000"))


def validate_settings() -> None:
    if not DATABASE_URL:
        raise RuntimeError("Missing required env var: DATABASE_URL")
    if not OPENAI_KEY:
        raise RuntimeError("Missing required env var: OPENAI_KEY")
    if not OPENAI_MODEL:
        raise RuntimeError("Missing required env var: OPENAI_MODEL")
    if MAX_LLM_INPUT_CHARS <= 0:
        raise RuntimeError("MAX_LLM_INPUT_CHARS must be > 0")
