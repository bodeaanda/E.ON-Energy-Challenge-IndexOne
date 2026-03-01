from sqlalchemy import Column, Integer, Numeric, String, DateTime
from sqlalchemy.sql import func
from .database import Base

class MeterReading(Base):
    __tablename__ = "meter_readings"

    id = Column(Integer, primary_key=True, index=True)
    reading_value = Column(Numeric(10, 2), nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    meter_id = Column(String(50), nullable=False)
    status = Column(String(50), default="SUCCESS")
