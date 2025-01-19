from aeris.db import DB


async def get_user_by_id(user_id: int) -> dict:
    async with DB() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
