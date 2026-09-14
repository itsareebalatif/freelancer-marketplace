import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.exceptions import AppError
from app.core.logging_config import setup_logging
from app.core.storage import UPLOAD_ROOT
from app.routers import auth, contracts, jobs, milestones, notifications, profiles, proposals, reviews, skills

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="Freelancer Marketplace API")

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_ROOT), name="uploads")


@app.exception_handler(AppError)
def handle_app_error(request: Request, exc: AppError):
    logger.warning(
        "%s %s -> %s [%s]: %s", request.method, request.url.path, exc.status_code, exc.code, exc.detail
    )
    return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "detail": exc.detail})


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, exc: Exception):
    logger.exception("%s %s -> unhandled error", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(skills.router)
app.include_router(jobs.router)
app.include_router(proposals.router)
app.include_router(contracts.router)
app.include_router(milestones.router)
app.include_router(reviews.router)
app.include_router(notifications.router)
