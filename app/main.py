# app/main.py
from fastapi import FastAPI
from app.accounts.routes import router as accounts_router
app = FastAPI(
    title="Movies homework",
    description="Description of project"
)

api_version_prefix = "/api/v1"

app.include_router(accounts_router, prefix=f"{api_version_prefix}/accounts", tags=["accounts"])
