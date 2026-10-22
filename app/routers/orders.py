from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order, Product
from app.schemas import OrderCreate, OrderOut, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["Orders"])
ALLOWED_STATUSES = {"pending", "confirmed", "cancelled", "delivered"}

@router.post("/", response_model=OrderOut, status_code=201)
def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    product = db.get(Product, data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Товар табылган жок")
    if product.stock < data.quantity:
        raise HTTPException(status_code=400, detail=f"Жетиштүү товар жок. Кампада: {product.stock}")
    product.stock -= data.quantity
    order = Order(
        customer_name=data.customer_name, phone=data.phone, address=data.address,
        product_id=product.id, quantity=data.quantity,
        total_price=round(product.price * data.quantity, 2), order_status="pending"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.get("/", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db)):
    return db.scalars(select(Order).order_by(Order.id.desc())).all()

@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ табылган жок")
    return order

@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(order_id: int, data: OrderStatusUpdate, db: Session = Depends(get_db)):
    if data.order_status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=422, detail=f"Статус төмөнкүлөрдүн бири болушу керек: {sorted(ALLOWED_STATUSES)}")
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ табылган жок")
    order.order_status = data.order_status
    db.commit()
    db.refresh(order)
    return order
