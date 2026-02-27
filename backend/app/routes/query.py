from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models import QueryRequest, QueryResponse

limiter = Limiter(key_func=get_remote_address)
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
@limiter.limit("20/minute")
async def run_query(request: Request, body: QueryRequest) -> QueryResponse:
    return QueryResponse(
        nodes=[],
        edges=[],
        rows=[],
        columns=[],
        truncated=False,
        row_count=0,
    )
