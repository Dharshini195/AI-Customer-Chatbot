from database import SessionLocal
from models import Message, Session, Order
from datetime import datetime


def add_message(session_id: int, role: str, content: str):
    db = SessionLocal()

    # ensure session exists
    session = db.query(Session).filter_by(session_id=session_id).first()
    if not session:
        session = Session(session_id=session_id)
        db.add(session)

    msg = Message(
        session_id=session_id,
        role=role,
        content=content
    )

    db.add(msg)
    db.commit()
    db.close()


def get_messages(session_id: int, limit: int = 10):
    db = SessionLocal()

    msgs = (
        db.query(Message)
        .filter_by(session_id=session_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )

    db.close()

    return [
        {"role": m.role, "content": m.content}
        for m in reversed(msgs)
    ]


def get_order_status(order_id: str):
    db = SessionLocal()

    order = db.query(Order).filter_by(order_id=order_id).first()
    db.close()

    return order.status if order else None
