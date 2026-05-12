from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from modules import Order
from datetime import datetime


def create_user(db: Session, order: dict):
    try:

        db_user = Order(
            item=order["item"], user_id=order["user_id"], order_date=order["order_date"]
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return {"message": "user created successfully", "statusCode": 201}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_orders(start_date: datetime, end_date: datetime, db: Session):
    try:
        query = db.query(Order)
        orders = query.filter(
            Order.order_date >= start_date, Order.order_date <= end_date
        ).all()
        return orders
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
