from contextlib import asynccontextmanager
from time import perf_counter
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.core.database import init_db
from src.core.logger import logger
from src.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    await init_db()
    logger.info("AI Hospital Operations System ready")
    yield


app = FastAPI(
    title="AI Hospital Operations Agent System",
    description="Multi-agent orchestrator managing beds, scheduling, emergency triage, billing, and inventory.",
    version="1.0.0",
    lifespan=lifespan
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started_at = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Request failed (method=%s, path=%s)", request.method, request.url.path)
        raise

    duration_ms = (perf_counter() - started_at) * 1000
    logger.info(
        "Request completed (method=%s, path=%s, status=%d, duration_ms=%.2f)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "AI Hospital Operations Agent"}