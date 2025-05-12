# main.py
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, Awaitable, Callable

import httpx
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


from core.config import PORT
from core.database import init_db
from core.scheduler import scheduler, setup_jobs
from routes import interviews
from services.logger import logger


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: Initialize database and start scheduler
    logger.info("Starting up...")
    try:
        await init_db()
        setup_jobs()
        scheduler.start()
        yield
    finally:
        # Shutdown: Stop scheduler
        scheduler.shutdown()
        logger.info("Scheduler shut down")


app = FastAPI(lifespan=lifespan)
app.title = "Interview API"
app.include_router(interviews.router, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Middleware to log incoming requests and their execution time.

    Args:
        request: The incoming HTTP request.
        call_next: A callable that takes a Request and returns an awaitable Response.

    Returns:
        The HTTP response after processing the request.
    """
    print(f"Request: {request.method} {request.url.path}")
    start_time = datetime.now()
    response = await call_next(request)
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    logger.info(
        f"Request: {request.method} {request.url.path} {response.status_code} " +
        f"from {request.client.host if request.client else 'unknown'} " +
        f"duration: {execution_time:.3f}s" 
    )
    return response


# Specific handler for HTTPException (optional, but good practice)
# This will catch FastAPI's own HTTPException and handle it before the generic Exception handler.
@app.exception_handler(httpx.HTTPStatusError)
async def http_exception_handler(request: Request, exc: httpx.HTTPStatusError) -> JSONResponse:
    """Handle HTTP exceptions raised by httpx.

    Args:
        request: The incoming HTTP request.
        exc: The HTTPStatusError exception raised by httpx.

    Returns:
        A JSONResponse with the error details and appropriate status code.
    """
    logger.warning(
        f"HTTP Exception: {exc.response.status_code} - {exc.response.text} for URL: {request.url}"
    )
    return JSONResponse(
        status_code=exc.response.status_code,
        content={"message": exc.response.text},
    )

# The "last hope" exception catcher
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    This handler catches any unhandled exceptions that are not
    caught by more specific exception handlers.
    """
    # Log the full traceback for debugging purposes (critical for production)
    logger.exception(f"Unhandled Exception for URL: {request.url} - {exc}")

    # Return a generic error message to the client for security
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "An unexpected error occurred. Please try again later."},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
