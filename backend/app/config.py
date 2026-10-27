import os

from dotenv import load_dotenv

load_dotenv()

SAMPLE_MODE = os.getenv("SAMPLE_MODE", "true").lower() == "true"