# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.accounts.routes import router as accounts_router
from app.cart.routes import router as cart_router
from app.orders.routes import router as order_router
from app.movies.routes import router as movies_router
from app.payments.routes import router as payment_router

app = FastAPI(title="Movies homework", description="Description of project")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_version_prefix = "/api/v1"

app.include_router(
    accounts_router, prefix=f"{api_version_prefix}/accounts", tags=["accounts"]
)
app.include_router(
    cart_router, prefix=f"{api_version_prefix}/carts", tags=["carts"]
)
app.include_router(
    movies_router, prefix=f"{api_version_prefix}/movies", tags=["movies"]
)
app.include_router(
    order_router, prefix=f"{api_version_prefix}/orders", tags=["orders"]
)
app.include_router(
    payment_router, prefix=f"{api_version_prefix}/payments", tags=["payments"]
)
