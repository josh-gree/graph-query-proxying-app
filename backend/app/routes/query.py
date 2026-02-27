import psycopg
from fastapi import APIRouter, Request
from psycopg.client_cursor import ClientCursor

from app.models import QueryRequest, QueryResponse
from app.query import executor, validator

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def run_query(request: Request, body: QueryRequest) -> QueryResponse:
    validator.validate(body.query)
    with psycopg.connect(request.app.state.database_url, cursor_factory=ClientCursor) as conn:
        return executor.execute(body.query, conn)
