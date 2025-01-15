from uuid import UUID

from asyncpg import Record

from aeris.db import DB


async def get_task_by_uuid(uuid: UUID, user_id: int) -> Record:
    async with DB() as conn:
        return await conn.fetchrow(
            "SELECT * FROM tasks WHERE uuid = $1 AND exists(SELECT 1 FROM user_projects WHERE user_id = $2 AND project_id = tasks.project_id)",
            uuid,
            user_id,
        )
