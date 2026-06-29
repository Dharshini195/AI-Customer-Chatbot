from crud import get_order_status as db_get_order_status


def order_status(order_id: str):
    status = db_get_order_status(order_id)

    if not status:
        return "No order found with this ID."

    # Convert DB status → human-friendly text
    STATUS_MAP = {
        "out_for_delivery": "Your order is out for delivery.",
        "shipped": "Your order has been shipped.",
        "cancelled": "Your order has been cancelled.",
        "refund_initiated": "Your refund has been initiated.",
        "pending": "Your order is being processed."
    }

    return STATUS_MAP.get(status, f"Order status: {status}")

def cancel_order(order_id : str):
    return f"Order {order_id} has been cancelled successfully. Refund will be initiated within 3-5 business days."

def create_ticket(order_id : str):
    return f"Ticket has been raised for order {order_id}. A Customer Support agent will reach out to you soon."
