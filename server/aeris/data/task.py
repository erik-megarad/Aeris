from uuid import UUID

from asyncpg import Record

from aeris.data.project import get_project_by_uuid
from aeris.db import DB


async def get_task_by_uuid(uuid: UUID, user_id: int) -> Record:
    async with DB() as conn:
        return await conn.fetchrow(
            "SELECT * FROM tasks WHERE uuid = $1 AND exists(SELECT 1 FROM user_projects WHERE user_id = $2 AND project_id = tasks.project_id)",
            uuid,
            user_id,
        )


async def create_task(project_id: UUID, user_id: int, name: str, input: str) -> Record | None:
    async with DB() as conn:
        project = await get_project_by_uuid(project_id, user_id)
        if not project:
            return None

        return await conn.fetchrow(
            "INSERT INTO tasks (project_id, name, input) VALUES ($1, $2, $3) RETURNING *",
            project["id"],
            name,
            input,
        )


async def update_task(
    uuid: UUID,
    user_id: int,
    name: str | None = None,
    input: str | None = None,
    state: str | None = None,
    result: str | None = None,
) -> Record | None:
    async with DB() as conn:
        task = await get_task_by_uuid(uuid, user_id)
        if not task:
            return None

        return await conn.fetchrow(
            "UPDATE tasks SET name = $1, input = $2, state = $3, result = $4 WHERE uuid = $5 RETURNING *",
            name,
            input,
            state,
            result,
            uuid,
        )


async def delete_task(uuid: UUID, user_id: int) -> Record | None:
    async with DB() as conn:
        task = await get_task_by_uuid(uuid, user_id)
        if not task:
            return None

        await conn.execute("DELETE FROM tasks WHERE uuid = $1", uuid)
        return task


async def create_task_embedding(task_id: int, embedding: list[float]) -> Record:
    async with DB() as conn:
        return await conn.fetchrow(
            "INSERT INTO task_embeddings (task_id, embedding) VALUES ($1, $2) RETURNING *",
            task_id,
            embedding,
        )


async def get_embeddings_for_task(task_id: int) -> list[Record]:
    async with DB() as conn:
        return await conn.fetch("SELECT * FROM task_embeddings WHERE task_id = $1", task_id)


async def get_metadata_for_task(task_id: int) -> Record:
    async with DB() as conn:
        return await conn.fetchrow("SELECT * FROM task_metadata WHERE task_id = $1", task_id)


async def find_similar_tasks(embedding: list[float]) -> list[Record]:
    async with DB() as conn:
        return await conn.fetch(
            """
                SELECT DISTINCT ON (embedding)
                  *, embedding <-> $1 AS similarity_score
                FROM task_embeddings
                INNER JOIN tasks ON task_embeddings.task_id = tasks.id
                WHERE embedding <-> $1 < 0.5
                ORDER BY embedding, embedding <-> $1
                LIMIT 5
            """,
            embedding,
        )
