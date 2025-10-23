"""
Twarga Cloud MVP - FastAPI Main Application
Entry point for the local cloud simulation lab
"""

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from datetime import datetime
from .database import init_db, check_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/events.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Twarga Cloud MVP",
    description="Local IaaS simulator for educational purposes",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
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

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Twarga Cloud MVP starting up...")
    logger.info(f"Startup time: {datetime.now().isoformat()}")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Continue running but log the error
    
    # Check database connection
    if check_db_connection():
        logger.info("Database connection verified")
    else:
        logger.warning("Database connection failed - some features may not work")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Twarga Cloud MVP shutting down...")
    logger.info(f"Shutdown time: {datetime.now().isoformat()}")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - redirects to login"""
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Admin panel page"""
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/monitor", response_class=HTMLResponse)
async def monitor_page(request: Request):
    """Monitoring page"""
    return templates.TemplateResponse("monitor.html", {"request": request})

@app.get("/soc", response_class=HTMLResponse)
async def soc_page(request: Request):
    """SOC dashboard page"""
    return templates.TemplateResponse("soc.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "twarga-cloud-mvp",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0"
    }

@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "name": "Twarga Cloud MVP API",
        "version": "0.1.0",
        "description": "Local IaaS simulator for educational purposes",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors"""
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {exc}")
    return templates.TemplateResponse("500.html", {"request": request}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )