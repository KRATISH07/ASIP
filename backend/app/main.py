from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.exceptions import ASIPException

# API Routers
from app.api.auth import router as auth_router
from app.api.incidents import router as incidents_router
from app.api.contractors import router as contractors_router
from app.api.notifications import router as notifications_router
from app.api.agent_logs import router as agent_logs_router
from app.api.dashboard import router as dashboard_router
from app.api.predict import router as predict_router

configure_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "ASIP Backend starting",
        version=settings.app_version,
        environment=settings.environment,
    )
    yield
    logger.info("ASIP Backend shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI Society Intelligence Platform — Multi-Agent AI Operations Center "
        "for residential communities. Powered by LangGraph, RAG, and ChromaDB."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(ASIPException)
async def asip_exception_handler(request: Request, exc: ASIPException):
    return JSONResponse(
        status_code=400,
        content={"error": exc.code, "message": exc.message},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred."},
    )


# Mount routers
app.include_router(auth_router)
app.include_router(incidents_router)
app.include_router(contractors_router)
app.include_router(notifications_router)
app.include_router(agent_logs_router)
app.include_router(dashboard_router)
app.include_router(predict_router)


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }
