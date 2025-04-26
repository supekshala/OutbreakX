from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router import router
from config.cors import add_cors_middleware


app = FastAPI()
add_cors_middleware(app)
app.include_router(router)
@app.get("/ping")
def ping():
    return {"message": "pong"}