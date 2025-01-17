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


async def create_project(user_id: int, name: str, description: str | None = None) -> Record:
    async with DB() as conn:
        project = await conn.fetchrow(
            "INSERT INTO projects (name, description) VALUES ($1, $2, $3) RETURNING *",
            name,
            user_id,
            description,
        )

        await conn.execute(
            "INSERT INTO user_projects (user_id, project_id) VALUES ($1, $2)",
            user_id,
            project["id"],
        )

        return project


async def update_project(
    uuid: UUID, user_id: int, name: str | None = None, description: str | None = None
) -> Record | None:
    async with DB() as conn:
        project = await get_project_by_uuid(uuid, user_id)
        if not project:
            return None

        return await conn.fetchrow(
            "UPDATE projects SET name = COALESCE($2, name), description = COALESCE($3, description) WHERE uuid = $1 RETURNING *",
            uuid,
            name,
            description,
        )


async def delete_project(uuid: UUID, user_id: int) -> Record | None:
    async with DB() as conn:
        project = await get_project_by_uuid(uuid, user_id)
        if not project:
            return None

        return await conn.fetchrow(
            "DELETE FROM projects WHERE uuid = $1 RETURNING *",
            uuid,
        )
