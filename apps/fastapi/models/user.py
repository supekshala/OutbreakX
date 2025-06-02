# app/models/user.py
from sqlalchemy import Column, String
from config.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)  # use 'sub' as ID
    email = Column(String, unique=True, index=True)
    name = Column(String)
