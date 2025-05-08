# models/record.py
from sqlalchemy import Column, String, Float
from core.database import Base

class Interview(Base):
    __tablename__ = "intervies"
    uuid = Column(String, primary_key=True, index=True)
    enumerator_id = Column(String)
    audit_url = Column(String, nullable=True)
    duration = Column(Float, nullable=True)