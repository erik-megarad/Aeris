import os

from dotenv import load_dotenv


def env():
    if os.environ.get("PYTEST_VERSION"):
        load_dotenv(dotenv_path=".env.test")
    else:
        load_dotenv()
