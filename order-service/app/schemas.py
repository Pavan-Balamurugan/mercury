import uuid
from datetime import datetime

from pydantic import BaseModel


class OrderItemIn(BaseModel):
    product_id: uuid.UUID
    quantity: int


class OrderCreate(BaseModel):
    user_id: uuid.UUID
    items: list[OrderItemIn]


class OrderItemOut(BaseModel):
    product_id: uuid.UUID
    quantity: int

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    created_at: datetime
    items: list[OrderItemOut]

    class Config:
        from_attributes = True