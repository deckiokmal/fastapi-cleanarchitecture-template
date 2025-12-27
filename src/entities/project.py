from sqlalchemy import Column, ForeignKey, String, Float, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from ..database.core import Base
from datetime import datetime, timezone


class Status(enum.Enum):
    PIPELINE = "Pipeline"
    RFI = 1
    PSA_GO = 2
    High = 3
    Top = 4
    

class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    budget = Column(Float, nullable=True)
    presales_name = Column(String, nullable=True)
    pss_name = Column(String, nullable=True)
    Status = Column(Enum(Status), nullable=False, default=Status.PIPELINE)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    customer_id = Column(UUID(as_uuid=True), ForeignKey('customers.id'), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'), nullable=False, index=True)
    created_at = Column(String, default=lambda: datetime.now(timezone.utc).isoformat())