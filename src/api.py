from fastapi import FastAPI
from src.auth.controller import router as auth_router
from src.users.controller import router as users_router
from src.users_settings.controller import router as users_settings_router
from src.daily_progress.controller import router as daily_progess_router

def register_routes(app: FastAPI) :
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(users_settings_router)
    app.include_router(daily_progess_router)
