from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Annotated
from geoalchemy2.shape import from_shape
from shapely import wkt
from shapely.geometry import Point, Polygon

#imports from folders
from models import models
from config.database import engine, SessionLocal
from schemas.schemas import PointCreate

app = FastAPI()

# Create tables from your models
models.Base.metadata.create_all(bind=engine)



# Dependency for DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]


@app.post("/shapes/")
def create_shape(shape: PointCreate, db: Session = Depends(get_db)):
    # Extract coordinates from the nested GeoJSON-like location field
    lon, lat = shape.location.coordinates
    shapely_geom = Point(lon, lat)

    db_shape = models.Point(
        location_point=from_shape(shapely_geom, srid=4326),
        description=shape.description
    )
    db.add(db_shape)
    db.commit()
    db.refresh(db_shape)
    return {"id": db_shape.id}


@app.get("/shapes")
def get_shapes(db: Session = Depends(get_db)):
    shapes = db.query(models.Point).all()
    results = []

    for shape in shapes:
        # Convert WKB to WKT, then to Shapely geometry
        shapely_geom = wkt.loads(db.scalar(shape.location_point.ST_AsText()))
        lon = shapely_geom.x
        lat = shapely_geom.y

        results.append({
            "id": shape.id,
            "location": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "description": shape.description
        })

    return results
