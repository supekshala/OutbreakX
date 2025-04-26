from fastapi import APIRouter
from api.endpoints.data import point  # Import the shapes router

router = APIRouter()

# Include the shapes router with a prefix
router.include_router(point.router, tags=["point"])