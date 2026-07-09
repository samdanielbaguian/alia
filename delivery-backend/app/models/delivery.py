from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    PICKED_UP = "picked_up"
    IN_DELIVERY = "in_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETURNED = "returned"


class Delivery(Base):
    __tablename__ = "deliveries"
    
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id"))
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING)
    assigned_at = Column(DateTime, nullable=True)
    picked_up_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    failed_reason = Column(Text, nullable=True)
    delivery_proof_image = Column(String(500), nullable=True)
    receiver_name = Column(String(100), nullable=True)
    receiver_signature = Column(String(500), nullable=True)
    delivery_attempts = Column(Integer, default=0)
    estimated_delivery_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Delivery {self.id}>"
