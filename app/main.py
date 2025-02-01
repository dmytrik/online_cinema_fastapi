# app/main.py
from fastapi import FastAPI
from app.accounts.routes import router as accounts_router
from app.cart.routes import router as cart_router
from app.orders.routes import router as order_router

app = FastAPI(title="Movies homework", description="Description of project")

api_version_prefix = "/api/v1"

app.include_router(
    accounts_router, prefix=f"{api_version_prefix}/accounts", tags=["accounts"]
)
app.include_router(
    cart_router, prefix=f"{api_version_prefix}/carts", tags=["carts"]
)
app.include_router(
    order_router, prefix=f"{api_version_prefix}/orders", tags=["orders"]
)
