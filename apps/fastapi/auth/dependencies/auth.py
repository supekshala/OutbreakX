# app/dependencies/auth.py

from fastapi import Depends, Request
from ..jwt_bearer import decode_jwt
from fastapi import HTTPException

async def get_current_user(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = auth.split(" ")[1]
    payload = decode_jwt(token)
    
    return {
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name")
    }
    
