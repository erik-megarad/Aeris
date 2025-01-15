from datetime import datetime, timezone
from typing import Optional

from bcrypt import checkpw, gensalt, hashpw
from pypika import Query, Table

from aeris.db import DB, init_db_pool


def hash_api_key(api_key, salt: Optional[bytes] = None):
    # Hash the API key
    salt = salt or gensalt()
    hashed = hashpw(api_key.encode(), salt)
    return hashed.decode()


async def create_api_key(user_id, project_id):
    import secrets

    # Generate a new API key
    raw_key = secrets.token_urlsafe(32)
    hashed_key = hash_api_key(raw_key)

    # Insert into the database
    api_keys = Table("api_keys")
    query = (
        Query.into(api_keys)
        .columns(api_keys.user_id, api_keys.project_id, api_keys.key)
        .insert(user_id, project_id, hashed_key)
    )

    async with DB() as conn:
        conn.execute(query.get_sql())

    return raw_key  # Return raw key to the user (not the hash!)


async def verify_api_key(api_key: str) -> dict[str, str]:
    await init_db_pool()

    api_keys = Table("api_keys")

    # Fetch the hashed key and associated fields
    query = (
        Query.from_(api_keys)
        .select(api_keys.user_id, api_keys.project_id, api_keys.key, api_keys.expires_at, api_keys.active)
        .where(api_keys.expires_at.isnull() | api_keys.expires_at >= datetime.now(timezone.utc))
        .where(api_keys.active == True)  # noqa: E712
    )

    async with DB() as conn:
        result = await conn.fetch(query.get_sql())

    # Loop through results and compare hashed keys (since keys are not unique)
    for row in result:
        user_id, project_id, hashed_key, expires_at, active = row

        try:
            if checkpw(api_key.encode(), hashed_key.encode()):
                # If match, validate other constraints
                if expires_at and expires_at < datetime.now(timezone.utc):
                    raise ValueError("API key has expired")

                # Return relevant user/project data
                return {"user_id": user_id, "project_id": project_id}
        except ValueError:
            # Invalid key or hash
            pass

    # If no match found
    raise ValueError("Invalid API key")
