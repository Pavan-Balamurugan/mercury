import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import Base, engine
from app.kafka_consumer import consume_payment_events
from app.kafka_producer import start_producer, stop_producer
from app.routes import router

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_producer()
    consumer_task = asyncio.create_task(consume_payment_events())
    yield
    consumer_task.cancel()
    await stop_producer()


app = FastAPI(title="Mercury - Order Service", lifespan=lifespan)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}