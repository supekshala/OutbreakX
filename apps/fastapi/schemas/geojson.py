from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from geojson_pydantic import (
    Feature,
    FeatureCollection,
    Point as GeoPoint,
    LineString,
    Polygon,
    MultiPoint,
    MultiLineString,
    MultiPolygon,
    GeometryCollection,
)
from pydantic import validator

# Union of all possible geometry types
Geometry = Union[
    GeoPoint,
    LineString,
    Polygon,
    MultiPoint,
    MultiLineString,
    MultiPolygon,
    GeometryCollection,
]

class FeatureProperties(BaseModel):
    type: str = ""  # Make type field optional with empty string as default
    # Allow any additional properties
    class Config:
        extra = "allow"

class GeoJSONFeature(Feature):
    """Extended GeoJSON Feature with type in properties"""
    properties: FeatureProperties

    @validator('geometry', pre=True)
    def validate_geometry(cls, v):
        if v is None:
            raise ValueError("geometry cannot be null")
        return v

class GeoJSONFeatureCollection(FeatureCollection):
    """Extended GeoJSON FeatureCollection"""
    features: List[GeoJSONFeature]

    @validator('features')
    def validate_features(cls, v):
        if not v:
            raise ValueError("features cannot be empty")
        return v

class FeatureResponse(BaseModel):
    status: str = "success"
    saved: int
