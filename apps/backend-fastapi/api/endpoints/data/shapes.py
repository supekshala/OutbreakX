# api/endpoints/shapes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape
from shapely import wkt
from shapely.geometry import Point
from models import models
from config.database import get_db
from schemas.schemas import PointCreate


router = APIRouter()

@router.post("/shapes")
def create_shape(shape: PointCreate, db: Session = Depends(get_db)):
    lon, lat = shape.location.coordinates
    geom = Point(lon, lat)
    db_shape = models.Point(
        location_point=from_shape(geom, srid=4326),
        description=shape.description
    )
    db.add(db_shape)
    db.commit()
    db.refresh(db_shape)
    return {
        "id": db_shape.id,
        "location": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "description": db_shape.description
    }

@router.get("/shapes/all")
def get_shapes(db: Session = Depends(get_db)):
    shapes = db.query(models.Point).all()
    results = []
    for shape in shapes:
        geom = wkt.loads(db.scalar(shape.location_point.ST_AsText()))
        results.append({
            "id": shape.id,
            "location": {
                "type": "Point",
                "coordinates": [geom.x, geom.y]
            },
            "description": shape.description
        })
    return results
