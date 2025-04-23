# Pydantic models
from pydantic import BaseModel, Field
from typing import Literal, List

class Location(BaseModel):
    type: Literal["Point"]
    coordinates: List[float]  # [longitude, latitude]

class PointCreate(BaseModel):
    location: Location
    description: str

class PolygonCoordinates(BaseModel):
    # A polygon is an array of coordinates (list of lists)
    coordinates: List[List[List[float]]]

class PolygonCreate(BaseModel):
    description: str
    geometry: PolygonCoordinates