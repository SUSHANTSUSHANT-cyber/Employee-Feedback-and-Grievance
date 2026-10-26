from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from .auth import initialize_admin
from .database import SessionLocal
from .routes import (
    admin_config,
    auth,
    categories,
    employees,
    interaction_logs,
    presets,
    sync,
    translation,
)


app = FastAPI(
    title="Employee Assistant API"
)


@app.on_event("startup")
def create_initial_admin():
    initialize_admin()


# =========================
# API ROUTES
# =========================
# Keep all API routers registered BEFORE the SPA fallback.

app.include_router(auth.router, prefix="/api")

app.include_router(
    sync.router,
    prefix="/api/rest"
)

app.include_router(
    employees.router,
    prefix="/api/rest"
)

app.include_router(
    categories.router,
    prefix="/api/rest"
)

app.include_router(
    presets.router,
    prefix="/api/rest"
)

app.include_router(
    interaction_logs.router,
    prefix="/api/rest"
)

app.include_router(
    interaction_logs.compat_router,
    prefix="/api/rest"
)

app.include_router(
    admin_config.router,
    prefix="/api/rest"
)

app.include_router(
    translation.router,
    prefix="/api/rest"
)


# =========================
# HEALTH CHECK
# =========================

@app.get("/health")
def health():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "ok"
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        ) from exc


# =========================
# ADMIN UI / STATIC FILES
# =========================

# Expected structure:
#
# api/
# ├── app/
# │   └── main.py
# └── static/
#     ├── index.html
#     └── assets/
#         ├── index-xxxxx.js
#         └── index-xxxxx.css
#

static_dir = Path(__file__).resolve().parents[1] / "static"
assets_dir = static_dir / "assets"
index_file = static_dir / "index.html"


# Serve Vite-generated JS, CSS, images, etc.
if assets_dir.is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=assets_dir),
        name="assets"
    )


# =========================
# ADMIN UI ROOT
# =========================

@app.get("/", include_in_schema=False)
def admin_ui_root():

    if index_file.is_file():
        return FileResponse(index_file)

    raise HTTPException(
        status_code=404,
        detail="Admin UI has not been built"
    )


# =========================
# SPA FALLBACK
# =========================
# This MUST be the last route in this file.
#
# It allows React routes such as:
# /employees
# /grievances
# /settings
#
# to return index.html, while /assets/... files are
# handled by the mounted StaticFiles route above.
#
# API routes are already registered before this fallback.

@app.get("/{path:path}", include_in_schema=False)
def admin_ui(path: str):

    # If a real static file exists directly inside api/static,
    # serve it.
    requested_file = static_dir / path

    if requested_file.is_file():
        return FileResponse(requested_file)

    # Otherwise return React/Vite index.html so the
    # frontend router can handle the route.
    if index_file.is_file():
        return FileResponse(index_file)

    raise HTTPException(
        status_code=404,
        detail="Admin UI has not been built"
    )
