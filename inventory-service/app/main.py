from fastapi import FastAPI

from app.db import Base, engine
from app.routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mercury - Inventory Service")

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}