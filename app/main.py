from fastapi import FastAPI

from app.api.routers import users, wallets

app = FastAPI()

app.include_router(users.router)
app.include_router(wallets.router)
