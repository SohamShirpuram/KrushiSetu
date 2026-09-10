from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse

from backend.database.init_db import init_db
from backend.api import (
    health_router,
    auth_router,
    chain_router,
    records_router,
    ai_router,
    ai_gp_router,
    ai_farmer_router,
    ai_warehouse_router,
    warehouse_storage_router,
    warehouse_dispatch_router,
)

# Path configuration
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
PAGES_DIR = FRONTEND_DIR / "pages"

app = FastAPI(
    title="KrushiSetu Platform API",
    description="AI-driven agricultural planning, crop production, warehouse, logistics and traceability platform.",
    version="1.0.0",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# APPLICATION LIFECYCLE (STARTUP & SHUTDOWN)
# =============================================================================

@app.on_event("startup")
def on_startup():
    """Ensure database schema is ready and pre-seeded on startup."""
    print("[+] KrushiSetu Backend Starting up: Initializing database & pre-seeding records...")
    init_db(seed=True)
    print("[+] KrushiSetu Backend Ready.")

@app.on_event("shutdown")
def on_shutdown():
    """Gracefully close resources, connections and clean up on shutdown."""
    print("[*] KrushiSetu Backend Shutting down: Cleaning up resources and closing active connections...")
    print("[*] KrushiSetu Backend Stopped.")

# Register API Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chain_router)
app.include_router(records_router)
app.include_router(ai_router)
app.include_router(ai_gp_router)
app.include_router(ai_farmer_router)
app.include_router(ai_warehouse_router)
app.include_router(warehouse_storage_router)
app.include_router(warehouse_dispatch_router)


# Mount frontend static directories
if FRONTEND_DIR.exists():
    uploads_dir = FRONTEND_DIR / "uploads" / "soil_reports"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    grain_dir = FRONTEND_DIR / "uploads" / "grain_samples"
    grain_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")
    app.mount("/uploads", StaticFiles(directory=str(FRONTEND_DIR / "uploads")), name="uploads")
    app.mount("/pages", StaticFiles(directory=str(PAGES_DIR)), name="pages")

# Portal Navigation Shortcuts
@app.get("/", include_in_schema=False)
def root_redirect():
    """Serves landing page."""
    index_file = PAGES_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Welcome to KrushiSetu API. Visit /docs for API documentation."}

@app.get("/login", include_in_schema=False)
def login_redirect():
    return RedirectResponse(url="/pages/login.html")

@app.get("/register", include_in_schema=False)
def register_redirect():
    return RedirectResponse(url="/pages/register.html")

@app.get("/dashboard", include_in_schema=False)
def dashboard_redirect():
    return RedirectResponse(url="/pages/dashboard.html")

