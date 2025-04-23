from fastapi import APIRouter

router = APIRouter()

@router.get("/mock-endpoint")
async def mock_endpoint():
    """
    Mock endpoint for demonstration purposes.
    """
    return {"message": "This is a mock endpoint!"}