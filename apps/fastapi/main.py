import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router import router
from config.database import check_db_connection, init_db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Database initialization on startup
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting application startup...")
    try:
        # Verify database connection first
        if not check_db_connection():
            logger.error("❌ Database connection check failed during startup")
            return
            
        logger.info("🔌 Database connection established successfully")
        
        # Initialize database tables
        if init_db():
            logger.info("✅ Database initialization completed successfully")
        else:
            logger.error("❌ Database initialization failed")
            
    except Exception as e:
        logger.error(f"❌ Error during startup: {str(e)}")
        # Don't raise the exception to allow the application to start
        # This is important for container environments like Choreo
        # that might restart the container on startup failure

# Health check endpoint with database status
@app.get("/api/v1/ping")
async def ping():
    db_status = "connected" if check_db_connection() else "disconnected"
    return {
        "status": "ok",
        "database": db_status
    }

# Include API router with version prefix
app.include_router(router, prefix="/api/v1")

# Root endpoint with health status
@app.get("/")
async def root():
    db_status = "connected" if check_db_connection() else "disconnected"
    return {
        "message": "OutbreakX API is running",
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "docs": "/docs",
        "openapi": "/openapi.json"
    }
