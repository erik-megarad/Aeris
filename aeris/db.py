import os

from asyncpg import Pool, create_pool
from bcrypt import gensalt, hashpw

from aeris.env import env

env()

DATABASE_URL = os.getenv("DATABASE_URL")


# Create a connection pool globally
_pool: Pool | None = None


async def init_db_pool():
    """
    Initializes the database connection pool.
    """
    global _pool
    if _pool is None:
        _pool = await create_pool(DATABASE_URL)


async def close_db_pool():
    """
    Closes the database connection pool.
    """
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


class DB:
    """
    A context manager for acquiring a database connection.
    Ensures that the connection is released back to the pool.
    """

    def __init__(self):
        if _pool is None:
            raise RuntimeError("Database pool not initialized. Call init_db_pool() first.")

    async def __aenter__(self):
        self.conn = await _pool.acquire()
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await _pool.release(self.conn)


async def drop_db():
    async with DB() as conn:
        await conn.execute("DROP TABLE IF EXISTS task_embeddings")
        await conn.execute("DROP TABLE IF EXISTS task_metadata")
        await conn.execute("DROP TABLE IF EXISTS events")
        await conn.execute("DROP TABLE IF EXISTS user_projects")
        await conn.execute("DROP TABLE IF EXISTS api_keys")
        await conn.execute("DROP TABLE IF EXISTS users")
        await conn.execute("DROP TABLE IF EXISTS task_tools")
        await conn.execute("DROP TABLE IF EXISTS tools")
        await conn.execute("DROP TABLE IF EXISTS tasks")
        await conn.execute("DROP TABLE IF EXISTS projects")


async def init_db():
    async with DB() as conn:
        await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                uuid UUID DEFAULT gen_random_uuid(),
                name TEXT NOT NULL, -- User-defined name of the project
                description TEXT, -- Optional description of the project
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                uuid UUID DEFAULT gen_random_uuid(),
                project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE, -- Links task to project
                name TEXT NOT NULL, -- User-defined name of the task
                input TEXT NOT NULL, -- Task input
                result TEXT, -- Final output of the task
                success BOOLEAN, -- Task success status, null is incomplete
                state TEXT NOT NULL DEFAULT 'PENDING', -- Task state (e.g., "PENDING", "RUNNING", "COMPLETED")
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        await conn.execute("""
            CREATE TABLE task_embeddings (
                id SERIAL PRIMARY KEY,
                uuid UUID DEFAULT gen_random_uuid(),
                task_id INT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE, -- Links embedding to task
                embedding VECTOR(1536) NOT NULL -- Vector representation of the task
            );
        """)

        await conn.execute("""
           CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                uuid UUID DEFAULT gen_random_uuid(),
                username TEXT UNIQUE NOT NULL, -- Unique identifier for the user (Must match github username)
                email TEXT UNIQUE, -- Email for user account (Must match github email)
                github_id TEXT UNIQUE, -- Optional GitHub ID for user account
                created_at TIMESTAMPTZ DEFAULT NOW() -- Timestamp of user creation
            );
        """)

        await conn.execute("""
            CREATE TABLE user_projects (
                user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- Links user to project
                project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE, -- Links user to project
                PRIMARY KEY (user_id, project_id)
            );
        """)

        await conn.execute("""
           CREATE TABLE task_metadata (
                id SERIAL PRIMARY KEY,
                uuid UUID DEFAULT gen_random_uuid(),
                task_id INT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE, -- Links to task
                key TEXT NOT NULL, -- Metadata key (e.g., "execution_time", "goals")
                value JSONB NOT NULL -- Metadata value (e.g., "12s", "['goal1', 'goal2']")
            );
        """)

        await conn.execute("""
            CREATE TABLE events (
                id SERIAL PRIMARY KEY,
                uuid UUID DEFAULT gen_random_uuid(),
                task_id INT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE, -- Links to task
                event_type TEXT NOT NULL, -- Type of event (e.g., "TASK_CREATED", "EMBEDDING_GENERATED")
                event_data JSONB NOT NULL, -- Payload associated with the event
                created_at TIMESTAMPTZ DEFAULT NOW() -- Timestamp of event creation
            );
        """)

        await conn.execute("""
            CREATE TABLE tools (
                id SERIAL PRIMARY KEY,
                uuid UUID DEFAULT gen_random_uuid(),
                name TEXT NOT NULL, -- Tool name
                description TEXT, -- Optional description of the tool
                parameters JSONB, -- Optional parameters for the tool
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        await conn.execute("""
            CREATE TABLE task_tools (
                task_id INT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                tool_id INT NOT NULL REFERENCES tools(id) ON DELETE CASCADE,
                PRIMARY KEY (task_id, tool_id)
            );
        """)

        await conn.execute("""
            CREATE TABLE api_keys (
                id SERIAL PRIMARY KEY,
                uuid UUID DEFAULT gen_random_uuid(), 
                user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- API key belongs to a user
                project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE, -- API key linked to a project
                key TEXT NOT NULL UNIQUE, -- The actual API key (hashed for security)
                created_at TIMESTAMPTZ DEFAULT NOW(), -- Timestamp when the key was created
                expires_at TIMESTAMPTZ, -- Optional expiration date
                active BOOLEAN DEFAULT TRUE -- Whether the key is currently active
            );
        """)

        await conn.execute("CREATE INDEX ON tasks (project_id);")
        await conn.execute("CREATE INDEX ON task_embeddings (task_id);")
        await conn.execute("CREATE INDEX ON user_projects (user_id);")
        await conn.execute("CREATE INDEX ON user_projects (project_id);")
        await conn.execute("CREATE INDEX ON task_metadata (task_id);")
        await conn.execute("CREATE INDEX ON events (task_id);")
        await conn.execute("CREATE INDEX ON task_tools (task_id);")
        await conn.execute("CREATE INDEX ON task_tools (tool_id);")

        await conn.execute("CREATE INDEX ON tasks (name);")
        await conn.execute("CREATE INDEX ON tasks (state);")
        await conn.execute("CREATE INDEX ON projects (name);")
        await conn.execute("CREATE INDEX ON users (username);")
        await conn.execute("CREATE INDEX ON tools (name);")

        await conn.execute("CREATE INDEX ON tasks (uuid);")
        await conn.execute("CREATE INDEX ON projects (uuid);")
        await conn.execute("CREATE INDEX ON users (uuid);")
        await conn.execute("CREATE INDEX ON task_embeddings (uuid);")
        await conn.execute("CREATE INDEX ON task_metadata (uuid);")
        await conn.execute("CREATE INDEX ON events (uuid);")
        await conn.execute("CREATE INDEX ON tools (uuid);")

        prod_flag = os.environ.get("ENVIRONMENT", "development") == "production"
        if not prod_flag:
            await conn.execute(
                "INSERT INTO users (username, email, github_id) VALUES ('erik-megarad', 'e@eriklp.com', '1234567890');"
            )
            await conn.execute(
                "INSERT INTO projects (uuid, name, description) VALUES ('36e8705e-6604-4e44-b58f-4e8c347a9f31', 'Test Project', 'A project for testing purposes');"
            )
            await conn.execute("INSERT INTO user_projects (user_id, project_id) VALUES (1, 1);")

            await conn.execute(
                "INSERT INTO tasks (uuid, project_id, name, input, state) VALUES ('123e4567-e89b-12d3-a456-426614174000', 1, 'Test Task', 'Test Input', 'PENDING');"
            )

            test_api_key = os.getenv("TEST_API_KEY", "TEST")

            hashed_api_key = hashpw(test_api_key.encode(), gensalt())
            await conn.execute(
                "INSERT INTO api_keys (user_id, project_id, key) VALUES (1, 1, $1);", hashed_api_key.decode()
            )


async def refresh_db():
    await init_db_pool()
    await drop_db()
    await init_db()
