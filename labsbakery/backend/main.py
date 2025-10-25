"""
🧁 LabsBakery Core - Main Application
FastAPI application entry point
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.config import get_settings
from backend.database import init_db
from backend.routes import projects

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    Runs on startup and shutdown
    """
    # Startup
    print("🧁 LabsBakery Core starting up...")
    print(f"📍 Version: {settings.app_version}")
    print(f"🗄️  Database: {settings.database_url}")
    
    # Initialize database
    init_db()
    
    yield
    
    # Shutdown
    print("👋 LabsBakery Core shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Build cyber labs like designing slides",
    lifespan=lifespan
)

# CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Templates
templates = Jinja2Templates(directory="frontend/templates")

# Include routers
app.include_router(projects.router)


@app.get("/")
async def root(request: Request):
    """Root endpoint - renders main builder page"""
    return templates.TemplateResponse(
        "builder.html",
        {"request": request, "title": "LabsBakery Core"}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version
    }


@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "endpoints": {
            "projects": "/api/projects",
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
