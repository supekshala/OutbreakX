# api/endpoints/shapes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely import wkt
from shapely.geometry import Point
from models import models
from config.database import get_db
from schemas.schemas import PointCreate
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from fastapi.logger import logger


router = APIRouter()


@router.post("/point")
def create_shape(shape: PointCreate, db: Session = Depends(get_db)):
    try:
        if not shape.location.coordinates or len(shape.location.coordinates) != 2:
            logger.error("Location coordinates are missing")
            raise HTTPException(
                status_code=400,
                detail="Coordinates must contain exactly two values (longitude and latitude).",
            )
        lon, lat = shape.location.coordinates
        geom = Point(lon, lat)
        db_shape = models.Point(
            location_point=from_shape(geom, srid=4326), description=shape.description
        )
        db.add(db_shape)
        db.commit()
        db.refresh(db_shape)
        logger.info(f"Shape created with ID: {db_shape.id}")
        return {
            "id": db_shape.id,
            "location": {"type": "Point", "coordinates": [lon, lat]},
            "description": db_shape.description,
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


@router.get("/point/all")
def get_shapes(db: Session = Depends(get_db)):
    shapes = db.query(models.Point).all()
    if not shapes:
        raise HTTPException(status_code=404, detail="No shapes found")
        logger.error("No shapes found in the database")
    results = []
    for shape in shapes:
        geom = wkt.loads(db.scalar(shape.location_point.ST_AsText()))
        results.append(
            {
                "id": shape.id,
                "location": {"type": "Point", "coordinates": [geom.x, geom.y]},
                "description": shape.description,
            }
        )
    return results
