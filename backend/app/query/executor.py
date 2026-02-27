import re

import psycopg
from age.age import AgeLoader, execCypher
from age.models import Edge as AgeEdge, Vertex
from psycopg.types import TypeInfo

from app.models import Edge, Node, QueryResponse

GRAPH_NAME = "dev"


def _parse_return_columns(query: str) -> list[str]:
    """Extract return variable names from the RETURN clause.

    Handles aliases (RETURN n AS person -> 'person'), property access
    (RETURN n.name -> 'name'), and simple variables (RETURN n -> 'n').
    Aggregations like count(n) must use an alias or they will fail AGE's
    identifier validation downstream.
    """
    match = re.search(
        r"\bRETURN\b\s+(.*?)(?=\s+\b(?:ORDER|LIMIT|SKIP|UNION)\b|$)",
        query,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ["v"]

    columns = []
    for part in match.group(1).strip().split(","):
        part = part.strip()
        alias = re.search(r"\bAS\s+(\w+)\s*$", part, re.IGNORECASE)
        if alias:
            columns.append(alias.group(1))
        else:
            columns.append(part.split(".")[-1].strip())
    return columns


def _register_age(conn: psycopg.Connection) -> None:
    """Set up AGE for a connection without LOAD 'age' (extension is pre-installed)."""
    with conn.cursor() as cursor:
        cursor.execute("SET search_path = ag_catalog, \"$user\", public;")
    ag_info = TypeInfo.fetch(conn, "agtype")
    conn.adapters.register_loader(ag_info.oid, AgeLoader)
    conn.adapters.register_loader(ag_info.array_oid, AgeLoader)


def execute(query: str, conn: psycopg.Connection) -> QueryResponse:
    """Execute a Cypher query via AGE and return a normalised QueryResponse."""
    _register_age(conn)

    columns = _parse_return_columns(query)
    cursor = execCypher(
        conn, GRAPH_NAME, query, cols=[f"{c} agtype" for c in columns]
    )

    nodes: dict[int, Node] = {}
    edges: dict[int, Edge] = {}
    rows: list[dict] = []

    for row in cursor:
        row_dict = {}
        for col, value in zip(columns, row):
            if isinstance(value, Vertex):
                if value.id not in nodes:
                    nodes[value.id] = Node(
                        id=value.id,
                        label=value.label,
                        properties=value.properties or {},
                    )
                row_dict[col] = value.id
            elif isinstance(value, AgeEdge):
                if value.id not in edges:
                    edges[value.id] = Edge(
                        id=value.id,
                        label=value.label,
                        start_id=value.start_id,
                        end_id=value.end_id,
                        properties=value.properties or {},
                    )
                row_dict[col] = value.id
            else:
                row_dict[col] = value
        rows.append(row_dict)

    return QueryResponse(
        nodes=list(nodes.values()),
        edges=list(edges.values()),
        rows=rows,
        columns=columns,
        truncated=False,
        row_count=len(rows),
    )
