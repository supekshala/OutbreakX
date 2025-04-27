from fastapi import FastAPI
from api.router import router
from config.cors import add_cors_middleware


app = FastAPI()
add_cors_middleware(app)


@app.get("/ping")
def ping():
    return {"message": "pong"}


app.include_router(router)
