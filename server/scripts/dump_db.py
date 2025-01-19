import asyncio
import os
from typing import List

import asyncpg

from aeris.env import env

env()

DATABASE_URL = os.getenv("DATABASE_URL")


async def dump_schema_to_file(database_url: str, output_file: str) -> None:
    conn = await asyncpg.connect(database_url)

    # Query tables and columns
    tables = await conn.fetch("""
        SELECT
            table_name,
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """)

    # Query constraints (foreign keys, primary keys, etc.)
    constraints = await conn.fetch("""
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            tc.constraint_type,
            tc.constraint_name
        FROM information_schema.table_constraints AS tc
        LEFT JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        LEFT JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
        WHERE tc.table_schema = 'public';
    """)

    table_columns: dict[str, List[asyncpg.Record]] = {}
    table_columns = {}
    for row in tables:
        table_columns.setdefault(row["table_name"], []).append(row)

    # Group constraints by table and type
    table_constraints: dict[str, dict[str, list[asyncpg.Record]]] = {}
    for row in constraints:
        table_constraints.setdefault(row["table_name"], {}).setdefault(row["constraint_type"], []).append(row)

    # Generate schema
    schema = []
    for table_name, columns in table_columns.items():
        schema.append(f"CREATE TABLE {table_name} (")
        column_defs = []
        for column in columns:
            col_def = f"    {column['column_name']} {column['data_type']}"
            if column["is_nullable"] == "NO":
                col_def += " NOT NULL"
            if column["column_default"]:
                col_def += f" DEFAULT {column['column_default']}"
            column_defs.append(col_def)
        schema.append(",\n".join(column_defs))

        # Add primary keys (handle composite keys)
        pk_constraints = table_constraints.get(table_name, {}).get("PRIMARY KEY", [])
        if pk_constraints:
            pk_columns = list(set([row["column_name"] for row in pk_constraints]))
            schema.append(f"    PRIMARY KEY ({', '.join(pk_columns)})")

        # Add foreign keys
        fk_constraints = table_constraints.get(table_name, {}).get("FOREIGN KEY", [])
        for fk in fk_constraints:
            schema.append(
                f"    FOREIGN KEY ({fk['column_name']}) REFERENCES {fk['foreign_table_name']}({fk['foreign_column_name']})"
            )

        schema.append(");\n")

    # Write to file
    with open(output_file, "w") as f:
        f.write("\n".join(schema))

    print(f"Schema dump saved to {output_file}")

    await conn.close()


if DATABASE_URL:
    asyncio.run(dump_schema_to_file(DATABASE_URL, "schema_dump.sql"))
