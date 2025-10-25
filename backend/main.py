"""
Twarga Cloud MVP - FastAPI Main Application
Entry point for the local cloud simulation lab
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uvicorn
import logging
from datetime import datetime
from .database import init_db, check_db_connection, get_db
from .auth import get_current_active_user, get_current_admin_user
from .models import User, VM, Event
from .schemas import (
    VMCreate, VMResponse, VMUpdate, VMAction, VMQuotaCheck,
    EventResponse, UserResponse
)
from .vm_manager import vm_manager

# Configure logging
import os
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'events.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
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

# ==================== VM API ENDPOINTS ====================

@app.post("/api/vms/quota-check", response_model=VMQuotaCheck)
async def check_vm_quota(
    vm_data: VMCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Check if user has enough credits to create VM"""
    can_create, message, cost = vm_manager.check_user_quota(
        db, current_user, vm_data.ram_mb, vm_data.disk_gb, vm_data.cpu_cores
    )
    
    return VMQuotaCheck(
        ram_mb=vm_data.ram_mb,
        disk_gb=vm_data.disk_gb,
        cpu_cores=vm_data.cpu_cores,
        estimated_cost=cost
    )

@app.post("/api/vms", response_model=VMResponse, status_code=status.HTTP_201_CREATED)
async def create_vm(
    vm_data: VMCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new VM"""
    
    # Check if VM name already exists for this user
    existing_vm = vm_manager.get_vm_by_name(db, vm_data.name, current_user.id)
    if existing_vm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"VM with name '{vm_data.name}' already exists"
        )
    
    # Create VM object
    vm = VM(
        name=vm_data.name,
        os_type=vm_data.os_type,
        ram_mb=vm_data.ram_mb,
        disk_gb=vm_data.disk_gb,
        cpu_cores=vm_data.cpu_cores,
        owner_id=current_user.id,
        status="pending"
    )
    
    db.add(vm)
    db.commit()
    db.refresh(vm)
    
    # Create VM with vm_manager (this includes quota check and credit deduction)
    success, message = vm_manager.create_vm(db, vm, current_user)
    
    if not success:
        # If VM creation failed, delete from database
        db.delete(vm)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    db.refresh(vm)
    logger.info(f"VM {vm.name} created successfully by user {current_user.username}")
    
    return vm

@app.get("/api/vms", response_model=List[VMResponse])
async def list_user_vms(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all VMs for the current user"""
    vms = vm_manager.list_user_vms(db, current_user.id)
    return vms

@app.get("/api/vms/{vm_id}", response_model=VMResponse)
async def get_vm(
    vm_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get VM details by ID"""
    vm = vm_manager.get_vm_by_id(db, vm_id)
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VM not found"
        )
    
    # Check if user owns this VM or is admin
    if vm.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this VM"
        )
    
    # Update uptime before returning
    vm_manager.update_vm_uptime(db, vm, current_user)
    db.refresh(vm)
    
    return vm

@app.patch("/api/vms/{vm_id}", response_model=VMResponse)
async def update_vm(
    vm_id: int,
    vm_data: VMUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update VM metadata"""
    vm = vm_manager.get_vm_by_id(db, vm_id)
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VM not found"
        )
    
    if vm.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this VM"
        )
    
    # Update metadata if provided
    if vm_data.vm_metadata:
        vm_manager.update_vm_metadata(db, vm, vm_data.vm_metadata)
    
    db.refresh(vm)
    return vm

@app.post("/api/vms/{vm_id}/action", response_model=dict)
async def vm_action(
    vm_id: int,
    action: VMAction,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Perform action on VM (start, stop, restart, destroy)"""
    vm = vm_manager.get_vm_by_id(db, vm_id)
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VM not found"
        )
    
    if vm.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to control this VM"
        )
    
    # Perform action
    success = False
    message = ""
    
    if action.action == "start":
        success, message = vm_manager.start_vm(db, vm, current_user)
    elif action.action == "stop":
        success, message = vm_manager.stop_vm(db, vm, current_user)
    elif action.action == "restart":
        success, message = vm_manager.stop_vm(db, vm, current_user)
        if success:
            success, message = vm_manager.start_vm(db, vm, current_user)
    elif action.action == "destroy":
        success, message = vm_manager.destroy_vm(db, vm, current_user)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return {"success": True, "message": message, "action": action.action}

@app.get("/api/vms/{vm_id}/status")
async def get_vm_status(
    vm_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current VM status"""
    vm = vm_manager.get_vm_by_id(db, vm_id)
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VM not found"
        )
    
    if vm.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this VM"
        )
    
    # Update status from vagrant
    vm_manager.update_vm_status(db, vm, current_user)
    db.refresh(vm)
    
    return {
        "vm_id": vm.id,
        "vm_name": vm.name,
        "status": vm.status,
        "ip_address": vm.ip_address,
        "uptime_seconds": vm.uptime_seconds
    }

# ==================== ADMIN VM ENDPOINTS ====================

@app.get("/api/admin/vms", response_model=List[VMResponse])
async def admin_list_all_vms(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin: List all VMs across all users"""
    vms = vm_manager.get_all_vms(db)
    return vms

@app.post("/api/admin/vms/{vm_id}/action", response_model=dict)
async def admin_vm_action(
    vm_id: int,
    action: VMAction,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin: Perform action on any VM"""
    vm = vm_manager.get_vm_by_id(db, vm_id)
    
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VM not found"
        )
    
    # Get VM owner
    owner = db.query(User).filter(User.id == vm.owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VM owner not found"
        )
    
    # Perform action
    success = False
    message = ""
    
    if action.action == "start":
        success, message = vm_manager.start_vm(db, vm, owner)
    elif action.action == "stop":
        success, message = vm_manager.stop_vm(db, vm, owner)
    elif action.action == "restart":
        success, message = vm_manager.stop_vm(db, vm, owner)
        if success:
            success, message = vm_manager.start_vm(db, vm, owner)
    elif action.action == "destroy":
        success, message = vm_manager.destroy_vm(db, vm, owner)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Log admin action
    event = Event(
        type="admin",
        severity="warning",
        message=f"Admin '{current_user.username}' performed {action.action} on VM '{vm.name}' (owner: {owner.username})",
        user_id=current_user.id,
        vm_id=vm.id,
        details={"action": action.action, "target_user": owner.username}
    )
    db.add(event)
    db.commit()
    
    return {"success": True, "message": message, "action": action.action}

# ==================== EVENT ENDPOINTS ====================

@app.get("/api/events", response_model=List[EventResponse])
async def list_user_events(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List events for the current user"""
    events = db.query(Event).filter(Event.user_id == current_user.id).order_by(Event.created_at.desc()).limit(limit).all()
    return events

@app.get("/api/admin/events", response_model=List[EventResponse])
async def admin_list_all_events(
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin: List all events"""
    events = db.query(Event).order_by(Event.created_at.desc()).limit(limit).all()
    return events

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )