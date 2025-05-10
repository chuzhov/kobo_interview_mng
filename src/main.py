# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from contextlib import asynccontextmanager
from datetime import datetime


from services.logger import logger
from core.database import init_db
from core.scheduler import scheduler, setup_jobs
from core.config import PORT
from routes.endpoints import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    setup_jobs()
    scheduler.start()
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):

    print(f"Request: {request.method} {request.url.path}")
    start_time = datetime.now()
    response = await call_next(request)
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()  
    logger.info(f" {request.method} {request.url.path} {response.status_code} Duration: {execution_time:.3f}s"
    )
    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)