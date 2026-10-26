from sqlalchemy import Column, String, Float, DateTime
from datetime import datetime
from app.core.database import Base

class Observation(Base):
    __tablename__ = "observations"

    id = Column(String, primary_key=True)
    station_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    temperature = Column(Float)
    pressure = Column(Float)
    humidity = Column(Float)
    qc_flag = Column(String)  # GOOD, SUSPECT, FAULTY
    flag_reason = Column(String)