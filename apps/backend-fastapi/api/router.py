from fastapi import APIRouter
from api.endpoints.data import point  # Import the shapes router
from api.endpoints.data import file_upload
from api.endpoints.data import polygon
from api.endpoints.data import p2p_routes
from api.endpoints.data import circle


router = APIRouter()

# Include the shapes router with a prefix
router.include_router(point.router, tags=["POINT"])
router.include_router(file_upload.router, tags=["FILE UPLOAD ENPOINTS"])
router.include_router(polygon.router, tags=["POLYGON"])
router.include_router(p2p_routes.router, tags=["POINT TO POINT ROUTES"]) 
router.include_router(circle.router, tags=["CIRCLE"])