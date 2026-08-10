import uuid

from pydantic import BaseModel


class StockSet(BaseModel):
    available_qty: int


class ReserveRequest(BaseModel):
    product_id: uuid.UUID
    quantity: int


class ReleaseRequest(BaseModel):
    product_id: uuid.UUID
    quantity: int


class InventoryOut(BaseModel):
    product_id: uuid.UUID
    available_qty: int
    reserved_qty: int

    class Config:
        from_attributes = True