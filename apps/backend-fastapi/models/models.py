from config.database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry



class Point(Base):
    __tablename__ = "shape"
    id = Column(Integer, primary_key=True, index=False)
    location_point = Column(Geometry(geometry_type='POINT', srid=4326))
    description = Column(String, index=True)