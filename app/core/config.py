from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL") if os.getenv("OPENAI_MODEL") else "gpt-5.4-mini"