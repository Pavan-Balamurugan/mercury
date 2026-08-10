import uuid

from sqlalchemy import Column, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


class Inventory(Base):
    __tablename__ = "inventory"

    product_id = Column(UUID(as_uuid=True), primary_key=True)
    available_qty = Column(Integer, nullable=False, default=0)
    reserved_qty = Column(Integer, nullable=False, default=0)