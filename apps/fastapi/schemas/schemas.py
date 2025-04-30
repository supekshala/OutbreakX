# Pydantic models
from pydantic import BaseModel
from typing import Literal, List


class Location(BaseModel):
    type: Literal["Point"]
    coordinates: Coordinate


class PointCreate(BaseModel):
    location: Location
    description: str
