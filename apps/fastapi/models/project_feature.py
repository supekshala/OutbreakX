from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from geoalchemy2 import Geometry
from config.database import Base

class ProjectFeature(Base):
    __tablename__ = "project_features"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=False, index=True)
    geometry = Column(Geometry(geometry_type='GEOMETRY', srid=4326), nullable=False)
    type = Column(String(50), nullable=False)
    properties = Column(JSONB, nullable=False, default={})
    
    def __repr__(self):
        return f"<ProjectFeature(id={self.id}, project_id={self.project_id}, type='{self.type}')>"
