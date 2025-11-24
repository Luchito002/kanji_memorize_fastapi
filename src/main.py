from fastapi import FastAPI
from src.api_response_error_handler import api_response_error_handler
from src.entities import *
from src.api import register_middlewares, register_routes
from src.logging import configure_logging, LogLevels

configure_logging(LogLevels.info)

app = FastAPI()

api_response_error_handler(app)
register_middlewares(app)
register_routes(app)
