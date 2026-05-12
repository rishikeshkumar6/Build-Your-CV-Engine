from fastapi import APIRouter, Depends
from datetime import datetime
from dependency import get_db
from sqlalchemy.orm import Session
from .order_service import create_user, get_orders

orderRouter = APIRouter(tags=["order"], prefix="/order")


@orderRouter.post("/create")
def create(order: dict, db: Session = Depends(get_db)):
    return create_user(db, order)


@orderRouter.get("/getorders")
def create(start_date: datetime, end_date=datetime, db: Session = Depends(get_db)):
    return get_orders(start_date, end_date, db)
