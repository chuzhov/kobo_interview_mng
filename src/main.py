# main.py
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
