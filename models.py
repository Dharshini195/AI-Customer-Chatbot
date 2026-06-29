from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from database import SessionLocal

class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(Integer, primary_key=True, index=True)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    last_active = Column(String, default=lambda: datetime.utcnow().isoformat())

    messages = relationship("Message", back_populates="session", cascade="all, delete")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.session_id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())

    session = relationship("Session", back_populates="messages")


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String, primary_key=True, index=True)
    customer_name = Column(String)
    status = Column(String)
    product = Column(String)
    phone = Column(String)
    email= Column(String)
    address = Column(String)
    created_at = Column(String)
    updated_at = Column(String)

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username      = Column(String, unique=True, index=True, nullable=False)
    email         = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role          = Column(String, default="user")        # "user" or "admin"
    is_active     = Column(Boolean, default=True)
    created_at    = Column(String, default=lambda: datetime.utcnow().isoformat())

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


def seed_orders():
    db = SessionLocal()

    now = datetime.utcnow().isoformat()

    orders = [
        {"order_id": "123", "customer_name": "John Doe", "product": "iPhone 15", "phone" : "9092847283", "email" : "dharshini1953@gmail.com","address" : "123 Main Street, FL", "status": "out_for_delivery"},
        {"order_id": "345", "customer_name": "Jane Smith", "product": "MacBook Pro", "phone" : "9092847283", "email" : "dharshini.s1953@gmail.com","address" : "456 South Street, MA", "status": "shipped"},
        {"order_id": "456", "customer_name": "Bob Wilson", "product": "AirPods Pro", "phone" : "9092847283", "email" : "dharshini1953@gmail.com","address" : "902 North Street, AL","status": "cancelled"},
        {"order_id": "789", "customer_name": "Alice Brown", "product": "iPad Mini", "phone" : "9092847283", "email" : "dharshini.s1953@gmail.com","address" : "102 Down Street, TX","status": "refund_initiated"},
        {"order_id": "999", "customer_name": "Charlie Davis", "product": "Apple Watch", "phone" : "9092847283", "email" : "dharshini1953@gmail.com","address" : "890 Town Street, AR","status": "pending"},
    ]

    for order_data in orders:
        # Check if already exists
        existing = db.query(Order).filter_by(order_id=order_data["order_id"]).first()

        if not existing:
            order = Order(
                order_id=order_data["order_id"],
                customer_name=order_data["customer_name"],
                product=order_data["product"],
                phone=order_data["phone"],
                email=order_data["email"],
                address=order_data["address"],
                status=order_data["status"],
                created_at=now,
                updated_at=now
            )
            db.add(order)

    db.commit()
    db.close()

    print("✅ Orders seeded successfully")