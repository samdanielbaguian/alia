from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class ShipmentStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Shipment(Base):
    __tablename__ = "shipments"
    
    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(50), unique=True, index=True)
    origin_address = Column(Text)
    destination_address = Column(Text)
    sender_name = Column(String(100))
    sender_phone = Column(String(20))
    recipient_name = Column(String(100))
    recipient_phone = Column(String(20))
    weight = Column(Float)  # in kg
    dimensions = Column(String(100))  # LxWxH format
    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.PENDING)
    estimated_delivery = Column(DateTime)
    actual_delivery = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<Shipment {self.tracking_number}>"
