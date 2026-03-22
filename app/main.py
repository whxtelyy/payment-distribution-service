import app.core.logging_config

import logging

from fastapi import FastAPI

from app.api.routers import auth, users, wallets
from app.core.sentry import init_sentry

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

init_sentry()
logger.info("Sentry успешно инициализирован с интеграцией FastAPI.")


app = FastAPI()

app.include_router(users.router)
app.include_router(wallets.router)
app.include_router(auth.router)
