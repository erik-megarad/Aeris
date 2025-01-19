import os
from typing import Any

from dotenv import load_dotenv


def env():
    if os.environ.get("PYTEST_VERSION"):
        load_dotenv(dotenv_path=".env.test")
    else:
        load_dotenv()


def get_setting(key: str, default: Any) -> str | Any:
    env()
    return os.environ.get(key, default)
