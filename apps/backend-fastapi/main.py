from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router import router


app = FastAPI()

app.include_router(router)