from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.auth.controller import router as auth_router
from src.users.controller import router as users_router
from src.users_settings.controller import router as users_settings_router
from src.daily_progress.controller import router as daily_progess_router
from src.kanjidraw.controller import router as kanji_matches_router
from src.srs.controller import router as srs_router

def register_routes(app: FastAPI) :
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(users_settings_router)
    app.include_router(daily_progess_router)
    app.include_router(kanji_matches_router)
    app.include_router(srs_router)

def register_middlewares(app: FastAPI):
    origins = [
        "http://localhost",
        "http://localhost:5173",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
