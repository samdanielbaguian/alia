from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class DriverStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_DUTY = "on_duty"
    OFF_DUTY = "off_duty"
    ON_LEAVE = "on_leave"


class Driver(Base):
    __tablename__ = "drivers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    phone = Column(String(20), unique=True)
    email = Column(String(100), unique=True, index=True)
    license_number = Column(String(50), unique=True)
    vehicle_number = Column(String(50))
    vehicle_type = Column(String(50))  # motorcycle, van, truck
    status = Column(Enum(DriverStatus), default=DriverStatus.OFF_DUTY)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    available_for_delivery = Column(Boolean, default=False)
    total_deliveries = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Driver {self.name}>"
