# 🌐 API

## POST /chat

Request:
{
  "session_id": 123,
  "query": "Where is my order?"
}

Response:
{
  "response": "Your order is out for delivery"
}

## GET /history/{session_id}

Returns conversation history.