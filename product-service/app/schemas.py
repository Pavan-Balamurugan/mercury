import uuid

from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    price: float
    category: str


class ProductOut(BaseModel):
    id: uuid.UUID
    name: str
    price: float
    category: str

    class Config:
        from_attributes = True