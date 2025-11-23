from fastapi import FastAPI
from src.api_response_error_handler import api_response_error_handler
from src.database.core import engine, Base
from src.entities import *
from src.api import register_middlewares, register_routes
from src.logging import configure_logging, LogLevels

configure_logging(LogLevels.info)

app = FastAPI()

"""
Only uncomment below to create new tables,
otherwise the tests will fail if not connected
"""

Base.metadata.create_all(bind=engine)

api_response_error_handler(app)
register_middlewares(app)
register_routes(app)
