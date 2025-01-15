from uuid import UUID

from asyncpg import Record

from aeris.db import DB


async def get_project_by_uuid(uuid: UUID, user_id: int) -> Record:
    async with DB() as conn:
        return await conn.fetchrow(
            "SELECT * FROM projects WHERE uuid = $1 AND exists(SELECT 1 FROM user_projects WHERE user_id = $2 AND project_id = projects.id)",
            uuid,
            user_id,
        )


async def get_projects(user_id: int, pagination: None = None) -> list[Record]:
    async with DB() as conn:
        return await conn.fetch(
            "SELECT * FROM projects WHERE exists(SELECT 1 FROM user_projects WHERE user_id = $1 AND project_id = projects.id)",
            user_id,
        )


async def get_tasks_for_project(
    project_uuid: UUID, user_id: int, pagination: None = None, filters: None = None
) -> list[Record]:
    project = await get_project_by_uuid(project_uuid, user_id)

    if not project:
        return []

    async with DB() as conn:
        return await conn.fetch(
            "SELECT * FROM tasks WHERE project_id = $1",
            project["id"],
        )
