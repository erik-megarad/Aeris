import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from aeris.db import init_db_pool, refresh_db  # noqa: E402


async def main():
    await init_db_pool()
    await refresh_db()


asyncio.run(main())
