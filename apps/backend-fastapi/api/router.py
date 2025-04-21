from fastapi import APIRouter
from api.endpoints.data import shapes  # Import the shapes router

router = APIRouter()

# Include the shapes router with a prefix
router.include_router(shapes.router, tags=["Shapes"])