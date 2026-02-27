import logging
import os

import age
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from psycopg_pool import ConnectionPool
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.routes import query, schema

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(query.router)
app.include_router(schema.router)


@app.on_event("startup")
async def startup() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")

    try:
        pool = ConnectionPool(database_url, open=True)
        with pool.connection() as conn:
            age.setUpAge(conn, "movies")
        app.state.pool = pool
        logger.info("Database connection pool established")
    except Exception as exc:
        logger.error("Failed to connect to database: %s", exc)
        raise


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})
