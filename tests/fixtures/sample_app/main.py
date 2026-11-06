"""Sample multi-route FastAPI app for end-to-end testing."""
from fastapi import FastAPI, Depends, Header
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    username: str
    email: str

class OrderPayload(BaseModel):
    item_id: str
    quantity: int

def verify_token(authorization: str = Header(...)):
    return authorization

@app.get("/health")
def health_check():
    """System health probe."""
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    """Prometheus metrics."""
    return {"latency": 0.05}

@app.get("/api/v1/users/{user_id}", tags=["users"])
def get_user_profile(user_id: str):
    """Retrieve public user profile."""
    return {"id": user_id, "username": "alice"}

@app.post("/api/v1/users", tags=["users"])
def create_user(user: UserCreate):
    """Register a new user account."""
    return {"id": "123", "username": user.username}

@app.post("/api/v1/orders", tags=["orders"])
def place_order(order: OrderPayload, token: str = Depends(verify_token)):
    """Place a customer order. Charges credit card and reserves stock."""
    return {"order_id": "ord_999", "status": "confirmed"}

@app.delete("/api/v1/orders/{order_id}", tags=["orders"])
def cancel_order(order_id: str, token: str = Depends(verify_token)):
    """Cancel and refund an existing order."""
    return {"order_id": order_id, "status": "cancelled"}
