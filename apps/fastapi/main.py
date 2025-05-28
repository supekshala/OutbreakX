from fastapi import FastAPI
from api.router import router
from config.cors import add_cors_middleware
from config.database import Base, engine


# creade the database tables according to the models.py
Base.metadata.create_all(bind=engine)


app = FastAPI()
add_cors_middleware(app)


@app.get("/ping")
def ping():
    return {"message": "pong"}


app.include_router(router, prefix="/api/v1")
