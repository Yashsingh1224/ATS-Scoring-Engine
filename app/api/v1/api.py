from fastapi import APIRouter
from app.api.v1.endpoints import matching

api_router = APIRouter()
api_router.include_router(matching.router, prefix="/matching", tags=["matching"])