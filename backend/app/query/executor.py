from psycopg_pool import ConnectionPool

from app.models import QueryResponse


def execute(query: str, pool: ConnectionPool) -> QueryResponse:
    """Execute a Cypher query via AGE and return a normalised QueryResponse."""
    return QueryResponse(
        nodes=[],
        edges=[],
        rows=[],
        columns=[],
        truncated=False,
        row_count=0,
    )
