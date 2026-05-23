"""
Main entry point for Healthcare AI Assistant
"""
import asyncio
import logging
import time
from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from dotenv import load_dotenv

from src.utils.config import Settings
from src.utils.logger import setup_logger

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
    PROMETHEUS_AVAILABLE = True
except Exception:
    PROMETHEUS_AVAILABLE = False
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

    def generate_latest():
        return b"# Prometheus client is not installed\n"

    Counter = None
    Histogram = None

# Load environment variables
load_dotenv()

# Initialize settings
settings = Settings()

# Setup logging
logger = setup_logger(__name__)

# Monitoring metrics
if PROMETHEUS_AVAILABLE:
    from prometheus_client import REGISTRY
    if "healthcare_api_requests_total" in REGISTRY._names_to_collectors:
        REQUEST_COUNT = REGISTRY._names_to_collectors["healthcare_api_requests_total"]
    else:
        REQUEST_COUNT = Counter(
            "healthcare_api_requests_total",
            "Total number of API requests",
            ["method", "path", "status_code"],
        )
    if "healthcare_api_request_latency_seconds" in REGISTRY._names_to_collectors:
        REQUEST_LATENCY = REGISTRY._names_to_collectors["healthcare_api_request_latency_seconds"]
    else:
        REQUEST_LATENCY = Histogram(
            "healthcare_api_request_latency_seconds",
            "API request latency in seconds",
            ["method", "path"],
            buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
        )
else:
    REQUEST_COUNT = None
    REQUEST_LATENCY = None


# Aggregated statistics tracker
class MetricsAggregator:
    """Track aggregated API and RAG performance metrics."""
    def __init__(self):
        self.query_count = 0
        self.embedding_api_calls = 0
        self.embedding_api_failures = 0
        self.rerank_api_calls = 0
        self.rerank_api_failures = 0
        self.llm_api_calls = 0
        self.llm_api_failures = 0
        self.total_embedding_ms = 0.0
        self.total_rerank_ms = 0.0
        self.total_llm_ms = 0.0
        self.total_query_ms = 0.0
    
    def to_dict(self):
        """Export metrics as dictionary."""
        return {
            "total_queries": self.query_count,
            "embedding": {
                "api_calls": self.embedding_api_calls,
                "api_failures": self.embedding_api_failures,
                "avg_latency_ms": round(self.total_embedding_ms / max(1, self.embedding_api_calls), 2),
            },
            "reranking": {
                "api_calls": self.rerank_api_calls,
                "api_failures": self.rerank_api_failures,
                "avg_latency_ms": round(self.total_rerank_ms / max(1, self.rerank_api_calls), 2),
            },
            "llm": {
                "api_calls": self.llm_api_calls,
                "api_failures": self.llm_api_failures,
                "avg_latency_ms": round(self.total_llm_ms / max(1, self.llm_api_calls), 2),
            },
            "rag": {
                "avg_query_latency_ms": round(self.total_query_ms / max(1, self.query_count), 2),
            },
        }


metrics_aggregator = MetricsAggregator()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Healthcare Knowledge Assistant for North Africa",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect request metrics for observability."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start

    if REQUEST_COUNT is not None:
        REQUEST_COUNT.labels(
            method=request.method,
            path=request.url.path,
            status_code=str(response.status_code),
        ).inc()

    if REQUEST_LATENCY is not None:
        REQUEST_LATENCY.labels(
            method=request.method,
            path=request.url.path,
        ).observe(elapsed)

    return response


@app.on_event("startup")
async def startup_event():
    """Initialize system components on startup"""
    logger.info("[START] Starting Healthcare AI Assistant...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"API Host: {settings.API_HOST}:{settings.API_PORT}")
    
    # TODO: Initialize ML models
    # TODO: Connect to databases
    # TODO: Load medical knowledge graph
    
    logger.info("[SUCCESS] System initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("[SHUTDOWN] Shutting down Healthcare AI Assistant...")
    
    # TODO: Close database connections
    # TODO: Save any pending data
    
    logger.info("[SUCCESS] Shutdown complete")


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    model_details = {}
    rag_loaded = False
    embedding_loaded = False
    reranker_loaded = False
    llm_loaded = False
    imaging_loaded = False
    imaging_model_info = {}

    try:
        from src.rag_system.api import rag_system as rag_runtime
        rag_loaded = rag_runtime is not None
    except Exception:
        rag_loaded = False

    try:
        from src.models.model_loader import get_model_loader
        model_details = get_model_loader().get_model_status()
        model_status = get_model_loader().get_status()
        embedding_loaded = bool(model_status.get("embedding_model_loaded", False))
        reranker_loaded = bool(model_status.get("reranker_loaded", False))
        llm_loaded = bool(model_status.get("llm_loaded", False))
    except Exception:
        model_details = {}
        embedding_loaded = False
        reranker_loaded = False
        llm_loaded = False

    try:
        from src.medical_imaging.api import classifier as imaging_runtime
        from src.medical_imaging.api import init_classifier
        
        # Initialize classifier if not already done
        if imaging_runtime is None:
            init_classifier()
            from src.medical_imaging.api import classifier as imaging_runtime
        
        imaging_loaded = imaging_runtime is not None
        
        # Get detailed imaging model status
        if imaging_runtime is not None:
            from pathlib import Path
            from src.medical_imaging.model_downloader import ModelDownloader
            
            # Get model information
            downloader = ModelDownloader()
            pretrained_path = Path("models/efficientnet_chest_pretrained.pt")
            model_info = downloader.get_model_info(pretrained_path)
            
            imaging_model_info = {
                "model_loaded": imaging_runtime.model_loaded,
                "using_mock": imaging_runtime.use_mock,
                "backbone": imaging_runtime.backbone,
                "num_classes": imaging_runtime.num_classes,
                "device": str(imaging_runtime.device),
                "pretrained_model": {
                    "exists": model_info.get("exists", False),
                    "path": model_info.get("path", ""),
                    "size_mb": model_info.get("size_mb", 0),
                    "num_parameters_millions": model_info.get("num_parameters_millions", 0)
                },
                "supported_diseases": len(imaging_runtime.DISEASES)
            }
    except Exception as e:
        imaging_loaded = False
        imaging_model_info = {"error": str(e)}

    return {
        "status": "healthy",
        "services": {
            "api": "active",
            "medical_imaging": "active" if settings.ENABLE_MEDICAL_IMAGING else "disabled",
            "rag_system": "active" if settings.ENABLE_RAG_SYSTEM else "disabled",
            "vital_signs": "active" if settings.ENABLE_VITAL_SIGNS else "disabled",
            "knowledge_graph": "active" if settings.ENABLE_KNOWLEDGE_GRAPH else "disabled",
        },
        "ai": {
            "rag_status": "ready" if rag_loaded else "not_initialized",
            "embedding_model_loaded": embedding_loaded,
            "reranker_loaded": reranker_loaded,
            "llm_loaded": llm_loaded,
            "imaging_model_loaded": imaging_loaded,
        },
        "ai_model": {
            **model_details,
            "api_first_mode": bool(getattr(settings, "MODEL_USE_API", False)),
            "llm_api_enabled": bool(getattr(settings, "LLM_USE_API", False)),
            "embedding_api_enabled": bool(getattr(settings, "EMBEDDINGS_USE_API", False)),
            "reranker_api_enabled": bool(getattr(settings, "RERANKER_USE_API", False)),
            "api_endpoints": {
                "llm": getattr(settings, "LLM_API_URL", ""),
                "embeddings": getattr(settings, "EMBEDDINGS_API_URL", ""),
                "reranker": getattr(settings, "RERANKER_API_URL", ""),
            },
        },
        "medical_imaging_model": imaging_model_info,
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    payload = generate_latest()
    return PlainTextResponse(content=payload.decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


@app.get("/metrics/stats")
async def metrics_stats():
    """
    Comprehensive RAG and API performance statistics.
    
    Returns detailed metrics for:
    - Query performance (p50, avg, success rate)
    - API reliability (success rates, fallback frequency)
    - Component latencies (embedding, rerank, LLM)
    - System health summary
    """
    try:
        from src.models.model_loader import get_model_loader
        loader = get_model_loader()
        api_latencies = {
            "embedding_api_ms": loader.last_embedding_api_ms,
            "rerank_api_ms": loader.last_rerank_api_ms,
            "llm_api_ms": loader.last_llm_api_ms,
        }
        
        # Calculate API success rates
        embedding_success_rate = round(
            100.0 * (1.0 - metrics_aggregator.embedding_api_failures / max(1, metrics_aggregator.embedding_api_calls)),
            2
        ) if metrics_aggregator.embedding_api_calls > 0 else 0.0
        
        rerank_success_rate = round(
            100.0 * (1.0 - metrics_aggregator.rerank_api_failures / max(1, metrics_aggregator.rerank_api_calls)),
            2
        ) if metrics_aggregator.rerank_api_calls > 0 else 0.0
        
        llm_success_rate = round(
            100.0 * (1.0 - metrics_aggregator.llm_api_failures / max(1, metrics_aggregator.llm_api_calls)),
            2
        ) if metrics_aggregator.llm_api_calls > 0 else 0.0
        
    except Exception as e:
        logger.warning("Could not retrieve API latencies: %s", e)
        api_latencies = {}
        embedding_success_rate = 0.0
        rerank_success_rate = 0.0
        llm_success_rate = 0.0
    
    # Build comprehensive stats response
    aggregated = metrics_aggregator.to_dict()
    
    return {
        "timestamp": time.time(),
        "system_status": "healthy" if metrics_aggregator.query_count > 0 else "idle",
        "aggregated_metrics": aggregated,
        "api_reliability": {
            "embedding": {
                "success_rate_percent": embedding_success_rate,
                "total_calls": metrics_aggregator.embedding_api_calls,
                "failures": metrics_aggregator.embedding_api_failures,
            },
            "reranking": {
                "success_rate_percent": rerank_success_rate,
                "total_calls": metrics_aggregator.rerank_api_calls,
                "failures": metrics_aggregator.rerank_api_failures,
            },
            "llm": {
                "success_rate_percent": llm_success_rate,
                "total_calls": metrics_aggregator.llm_api_calls,
                "failures": metrics_aggregator.llm_api_failures,
            },
        },
        "last_api_latencies_ms": api_latencies,
        "prometheus_enabled": PROMETHEUS_AVAILABLE,
        "documentation": {
            "endpoint": "/metrics/stats",
            "refresh_interval_seconds": 10,
            "note": "Metrics reset on server restart. Use Prometheus endpoint (/metrics) for long-term monitoring."
        }
    }


# Add API routers
try:
    if settings.ENABLE_MEDICAL_IMAGING:
        from src.medical_imaging.api import router as imaging_router
        app.include_router(imaging_router, prefix="/api/v1/imaging", tags=["Medical Imaging"])
        logger.info("Medical Imaging API enabled")
except Exception as e:
    logger.warning(f"Could not load Medical Imaging API: {e}")

try:
    from src.medical_imaging.simple_analyze_api import router as image_analyze_router
    app.include_router(image_analyze_router, prefix="/api/v1/image", tags=["Medical Imaging"])
    logger.info("Lightweight image analyze API enabled")
except Exception as e:
    logger.warning(f"Could not load lightweight image analyze API: {e}")

try:
    if settings.ENABLE_RAG_SYSTEM:
        from src.rag_system.api import router as rag_router, chat_router
        app.include_router(rag_router, prefix="/api/v1/rag", tags=["Knowledge Retrieval"])
        app.include_router(chat_router, prefix="/api/v1", tags=["Knowledge Retrieval"])
        logger.info("RAG System API enabled")
except Exception as e:
    logger.warning(f"Could not load RAG API: {e}")

try:
    if settings.ENABLE_VITAL_SIGNS:
        from src.vital_signs.api import router as vitals_router
        app.include_router(vitals_router, prefix="/api/v1/vitals", tags=["Vital Signs"])
        logger.info("Vital Signs API enabled")
except Exception as e:
    logger.warning(f"Could not load Vital Signs API: {e}")

try:
    from src.auth.router import router as auth_router
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    logger.info("Authentication API enabled")
except Exception as e:
    logger.warning(f"Could not load Authentication API: {e}")

try:
    from src.admin.router import router as admin_router
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
    logger.info("Admin API enabled")
except Exception as e:
    logger.warning(f"Could not load Admin API: {e}")

try:
    # Include classical models API if present
    from src.classical_models.api import router as classical_router
    app.include_router(classical_router, prefix="/api/v1/classical", tags=["Classical Models"])
    logger.info("Classical models API enabled")
except Exception as e:
    logger.warning(f"Could not load Classical Models API: {e}")

# Mount example accounts API (from backend_examples) if available so the dashboard can fetch summaries
try:
    from backend_examples import accounts_api as accounts_example
    # Mount at root so the example's declared path `/api/v1/accounts/{id}/summary`
    # remains addressable as `/api/v1/accounts/...` when included in the main app.
    app.mount("/", accounts_example.app)
    logger.info("Mounted example accounts API at /")
except Exception as e:
    logger.info(f"Example accounts API not mounted: {e}")

# Ensure account summary endpoint is reachable through the main app (proxy to example)
try:
    from backend_examples.accounts_api import account_summary as _account_summary

    @app.get('/api/v1/accounts/{account_id}/summary')
    async def account_summary_proxy(account_id: str):
        return await _account_summary(account_id)

    logger.info('Registered account summary proxy endpoint')
except Exception:
    logger.info('Could not register account summary proxy endpoint')


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"},
    )


def run_application():
    """Run the FastAPI application"""
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        workers=settings.API_WORKERS if not settings.API_RELOAD else 1,
        log_level=settings.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    run_application()
