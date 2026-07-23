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
from app.api.decision import router as decision_router
from app.api.feedback import router as feedback_router
from app.api.analytics import router as analytics_router
from app.api.sensor_buffer import router as sensor_buffer_router
from app.api.complaints import router as complaints_router

configure_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "ASIP Backend starting",
        version=settings.app_version,
        environment=settings.environment,
    )
    # Initialize LangGraph PostgreSQL checkpointer tables in non-testing environments
    import sys
    if settings.environment != "testing" and "pytest" not in sys.modules:
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            conn_string = settings.database_url.replace("+asyncpg", "")
            
            # Enter the context manager manually so connection pool stays active across requests
            context_manager = AsyncPostgresSaver.from_conn_string(conn_string)
            saver = await context_manager.__aenter__()
            await saver.setup()
            
            # Register checkpointer globally in graph module
            from app.agents.graph import set_global_checkpointer
            set_global_checkpointer(saver)
            
            app.state.checkpointer_context = context_manager
            
            logger.info("LangGraph PostgreSQL checkpointer tables initialized and registered successfully")
        except Exception as e:
            logger.error("Failed to initialize LangGraph PostgreSQL checkpointer tables", error=str(e))
    yield
    
    # Clean up checkpointer connections on shutdown
    if hasattr(app.state, "checkpointer_context"):
        logger.info("Closing LangGraph PostgreSQL checkpointer connections")
        try:
            await app.state.checkpointer_context.__aexit__(None, None, None)
        except Exception as e:
            logger.error("Failed to close checkpointer context manager", error=str(e))
            
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

from app.core.tenant_middleware import TenantMiddleware
app.add_middleware(TenantMiddleware)



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
app.include_router(decision_router)
app.include_router(feedback_router)
app.include_router(analytics_router)
app.include_router(sensor_buffer_router)
app.include_router(complaints_router)


@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }
