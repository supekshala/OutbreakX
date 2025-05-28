from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router import router
from config.database import Base, engine

# Create the database tables according to the models.py
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OutbreakX API",
    description="API for OutbreakX application",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/ping")
async def ping():
    return {"message": "pong"}

# Include API router with version prefix
app.include_router(router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "OutbreakX API is running",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }
