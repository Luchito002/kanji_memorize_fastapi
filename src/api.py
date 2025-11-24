from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.auth.controller import router as auth_router
from src.users.controller import router as users_router
from src.users_settings.controller import router as users_settings_router
from src.daily_progress.controller import router as daily_progess_router
from src.kanjidraw.controller import router as kanji_matches_router
from src.users_stories.controller import router as users_stories_router
from src.users_preferences.controller import router as users_preferences_router
from src.fsrs.controller import router as fsrs_router
from src.daily_fsrs_progress.controller import router as daily_fsrs_progress_router
from src.quick_test.controller import router as quick_test_router

def register_routes(app: FastAPI) :
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(users_settings_router)
    app.include_router(daily_progess_router)
    app.include_router(kanji_matches_router)
    app.include_router(users_stories_router)
    app.include_router(users_preferences_router)
    app.include_router(fsrs_router)
    app.include_router(daily_fsrs_progress_router)
    app.include_router(quick_test_router)

def register_middlewares(app: FastAPI):
    origins = [
        "http://localhost",
        "http://localhost:5173",
        "https://kanji-memorize.vercel.app"
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
