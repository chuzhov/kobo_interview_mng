# models/record.py
from sqlalchemy import Column, String, Float
from core.database import Base

class Interview(Base):
    __tablename__ = "intervies"
    uuid = Column(String, primary_key=True, index=True)
    enumerator_Id = Column(String)
    audit_URL = Column(String, nullable=True)
    interview_duration = Column(Float, nullable=True)