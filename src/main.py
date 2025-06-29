from fastapi import FastAPI
from src.database.core import engine, Base
from src.entities import *
from src.api import register_routes
from src.logging import configure_logging, LogLevels
from fastapi.middleware.cors import CORSMiddleware

configure_logging(LogLevels.info)

print("✅ Starting FastAPI app...")
app = FastAPI()

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

"""
Only uncomment below to create new tables,
otherwise the tests will fail if not connected
"""

Base.metadata.create_all(bind=engine)

register_routes(app)
