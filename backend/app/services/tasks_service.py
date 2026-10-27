"""Look up open tasks for given owners in the Zetaris tasks table."""

import os
import re

from app.services import zetaris_client

DEFAULT_TABLE = "recallai_data.tasks"

# Change these if your table uses different column names.
ID_COL = "id"
TITLE_COL = "title"
OWNER_COL = "owner"
STATUS_COL = "status"

CLOSED_STATUSES = ("done",)

_TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")


def _quote(value: str) -> str:
    """Escape a value so it is safe inside a SQL string literal."""
    value = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{value}'"


def _table_name() -> str:
    table = os.getenv("ZETARIS_TASKS_TABLE", DEFAULT_TABLE)
    if not _TABLE_RE.match(table):
        raise zetaris_client.ZetarisError("ZETARIS_TASKS_TABLE is not a valid name.")
    return table


def get_open_tasks(owners: list) -> list:
    """Return open (not done) tasks whose owner is in `owners`."""
    owners = [o for o in owners if o and o.strip()]
    if not owners:
        return []

    owner_list = ", ".join(_quote(o.strip().lower()) for o in owners)
    closed_list = ", ".join(_quote(s) for s in CLOSED_STATUSES)

    sql = (
        f"SELECT {ID_COL}, {TITLE_COL}, {OWNER_COL}, {STATUS_COL} "
        f"FROM {_table_name()} "
        f"WHERE LOWER({OWNER_COL}) IN ({owner_list}) "
        f"AND LOWER({STATUS_COL}) NOT IN ({closed_list}) "
        f"ORDER BY {ID_COL}"
    )
    rows = zetaris_client.run_sql(sql, limit=1000)

    return [
        {"id": r[0], "title": r[1], "owner": r[2], "status": r[3]}
        for r in rows
        if len(r) >= 4
    ]