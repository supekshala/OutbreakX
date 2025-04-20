# Pydantic models
from pydantic import BaseModel, Field
from typing import Literal, List

class Location(BaseModel):
    type: Literal["Point"]
    coordinates: List[float]  # [longitude, latitude]

class PointCreate(BaseModel):
    location: Location
    description: str