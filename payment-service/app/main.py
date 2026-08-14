import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db import Base, engine
from app.kafka_consumer import consume_order_events
from app.kafka_producer import start_producer, stop_producer

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_producer()
    consumer_task = asyncio.create_task(consume_order_events())
    yield
    consumer_task.cancel()
    await stop_producer()


app = FastAPI(title="Mercury - Payment Service", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}