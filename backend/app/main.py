import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.routes import query, schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    app.state.database_url = database_url
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(query.router)
app.include_router(schema.router)


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})
