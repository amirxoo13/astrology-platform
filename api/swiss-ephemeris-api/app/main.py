from contextlib import asynccontextmanager
import time
import uuid
import traceback

import swisseph as swe

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __app_name__, __version__
from app.core.config import settings
from app.core.logging_config import setup_logging, app_logger as log
from app.api.v1.router import router as v1_router
from app.deps import init_core, get_swiss_core
from app.schemas.common import ErrorResponse


AGPL_NOTICE = (
    "This project is based on Swiss Ephemeris by Astrodienst AG and is released\n"
    "under the GNU Affero General Public License (AGPL-3.0-or-later).\n"
    "Source code must always be public and match the code running on this server.\n"
    "Source: https://github.com/devtrongle/swiss-ephemeris-api"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    log.info("app_startup", ephe_path=settings.ephe_path, log_level=settings.log_level)
    swe.set_ephe_path(settings.ephe_path)
    init_core()
    yield
    log.info("app_shutdown")


def _http_status_label(code: int) -> str:
    labels = {
        400: "Bad Request",
        404: "Not Found",
        405: "Method Not Allowed",
        422: "Validation Error",
        500: "Internal Server Error",
        503: "Service Unavailable",
    }
    return labels.get(code, f"HTTP Error {code}")


def _format_traceback(exc: Exception) -> str:
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-1000:]


def create_app() -> FastAPI:
    app = FastAPI(
        title=__app_name__,
        version=__version__,
        description="REST API for Swiss Ephemeris astronomical calculations. "
        "Comprehensive coverage: planets, houses, lunar nodes, fixed stars, eclipses, and lunar phases.",
        license_info={"name": "AGPL-3.0-or-later", "url": "https://www.gnu.org/licenses/agpl-3.0.html"},
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request middleware — logs every request with timing
    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        start = time.perf_counter()
        response = None
        try:
            response = await call_next(request)
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            log.info(
                "http_request",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status=response.status_code if response else "never_started",
                elapsed_ms=elapsed_ms,
            )
        return response

    # HTTPException handler — uniform error shape
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        log.warning(
            "http_exception",
            request_id=request_id,
            status_code=exc.status_code,
            detail=exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=_http_status_label(exc.status_code),
                detail=exc.detail,
                code=f"HTTP_{exc.status_code}",
            ).model_dump(),
        )

    # Unhandled exception handler — catches everything else (swisseph crashes, etc.)
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        log.error(
            "unhandled_exception",
            request_id=request_id,
            exc_type=type(exc).__name__,
            exc_msg=str(exc),
            exc_traceback=_format_traceback(exc),
        )
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal Server Error",
                detail="An unexpected error occurred. If the problem persists, please report it.",
                code="INTERNAL_ERROR",
            ).model_dump(),
        )

    # v1 routes
    app.include_router(v1_router)

    @app.get("/", tags=["info"])
    async def root() -> dict:
        return {
            "name": __app_name__,
            "version": __version__,
            "license": "AGPL-3.0-or-later",
            "notice": AGPL_NOTICE,
            "docs": "/docs",
            "redoc": "/redoc",
        }

    @app.get("/health", tags=["info"])
    async def health() -> dict:
        try:
            get_swiss_core()
            return {
                "status": "ok",
                "ephe_path": settings.ephe_path,
                "source": "https://github.com/devtrongle/swiss-ephemeris-api",
            }
        except Exception as e:
            log.error("health_check_failed", error=str(e))
            raise HTTPException(status_code=503, detail=f"Swiss Ephemeris not available: {e}")

    return app


app = create_app()
