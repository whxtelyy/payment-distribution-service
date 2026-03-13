import app.core.logging_config

from fastapi import FastAPI

from app.api.routers import auth, users, wallets

app = FastAPI()

app.include_router(users.router)
app.include_router(wallets.router)
app.include_router(auth.router)