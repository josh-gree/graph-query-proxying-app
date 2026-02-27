from typing import Any

from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str


class Node(BaseModel):
    id: int
    label: str
    properties: dict[str, Any]


class Edge(BaseModel):
    id: int
    label: str
    start_id: int
    end_id: int
    properties: dict[str, Any]


class QueryResponse(BaseModel):
    nodes: list[Node]
    edges: list[Edge]
    rows: list[dict[str, Any]]
    columns: list[str]
    truncated: bool
    row_count: int


class SchemaResponse(BaseModel):
    labels: list[str]
    relationship_types: list[str]
    property_keys: list[str]
