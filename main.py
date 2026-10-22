from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import Base, engine
from app import models
from app.routers import products, orders, ai

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Glovo Delivery API",
    description="Товарлар, заказдар жана Gemini AI жардамчысы",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(products.router)
app.include_router(orders.router)
app.include_router(ai.router)

@app.get("/")
def root():
    return {"message": "Glovo Delivery API иштеп жатат", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}
