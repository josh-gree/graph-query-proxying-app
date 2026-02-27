from fastapi import APIRouter

from app.models import SchemaResponse

router = APIRouter()


@router.get("/schema", response_model=SchemaResponse)
async def get_schema() -> SchemaResponse:
    return SchemaResponse(
        labels=[],
        relationship_types=[],
        property_keys=[],
    )
