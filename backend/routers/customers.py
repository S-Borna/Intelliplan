"""Customer management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Customer
from backend.schemas import CustomerCreate, CustomerOut

router = APIRouter(prefix="/api/customers", tags=["Customers"])


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer."""
    existing = db.query(Customer).filter(Customer.email == data.email).first()
    if existing:
        raise HTTPException(400, "Customer with this email already exists")

    customer = Customer(**data.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    """List all customers."""
    return db.query(Customer).order_by(Customer.name).all()


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """Get customer details."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(404, "Customer not found")
    return customer
