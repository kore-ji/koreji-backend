import uuid
from fastAPI import APIRouter

router = APIRouter(prefix="/api/records", tags=["records"])

@router.get("/")
async def get_records():
    pass

@router.post("/")
async def create_record():
    pass

@router.put("/{record_id}")
async def update_record(id: uuid.UUID):
    pass