from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from src.api_response import APIResponse

def api_response_error_handler(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        print("HOLIWIS DESDE HTTPEXCEPTION")
        return JSONResponse(
            status_code=exc.status_code,
            content=APIResponse(
                status="error",
                message=exc.detail,
                result=None
            ).dict()
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=APIResponse(
                status="error",
                message="Validation error",
                result=exc.errors()
            ).dict()
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content=APIResponse(
                status="error",
                message="Internal server error",
                result=None
            ).dict()
        )
