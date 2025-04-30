from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon
from schemas.schemas import PolygonCreate
from config.database import get_db
from sqlalchemy.exc import SQLAlchemyError
from models import models
import logging

# Initialize logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


router = APIRouter()


@router.post("/polygon")
def create_polygon(shape: PolygonCreate, db: Session = Depends(get_db)):
    try:
        # Log the incoming request body for debugging purposes
        logger.debug(f"Received Polygon data: {shape}")

        # Convert the list of coordinates into a Shapely Polygon object
        # The coordinates list should be passed directly without using a 'geometry' keyword
        geom = Polygon(shape.geometry.coordinates[0])  # First ring of coordinates

        # Log the geometry to verify its creation
        logger.debug(f"Created Polygon geometry: {geom}")

        # Create a new Polygon entry in the database (note that this is your database model, not Shapely's)
        db_polygon = models.Polygon(
            geometry=from_shape(
                geom, srid=4326
            ),  # Convert to PostGIS-compatible geometry
            description=shape.description,
        )

        # Add and commit to the database
        db.add(db_polygon)
        db.commit()
        db.refresh(db_polygon)

        # Return success response
        return {"id": db_polygon.id, "description": db_polygon.description}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(
            status_code=400, detail=f"Error processing the request: {e}"
        )
