"""
Twarga Cloud MVP - FastAPI Main Application
Entry point for the local cloud simulation lab
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status, Query, Body
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import logging
from datetime import datetime, timedelta
from .database import init_db, check_db_connection, get_db
from .auth import (
    get_current_active_user, get_current_admin_user, 
    get_password_hash, authenticate_user, create_access_token,
    get_user_by_username, ACCESS_TOKEN_EXPIRE_MINUTES
)
from .models import User, VM, Event
from .schemas import (
    VMCreate, VMResponse, VMUpdate, VMAction, VMQuotaCheck,
    EventResponse, UserResponse, UserCreate, UserLogin, Token
)
from .vm_manager import vm_manager
from .monitor import system_monitor
from .soc import soc_manager

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

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page"""
    return templates.TemplateResponse("register.html", {"request": request})

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

# ==================== AUTHENTICATION API ENDPOINTS ====================

@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    # Check if username already exists
    existing_user = get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_admin=False,
        credits=100  # Starting credits
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Log registration event
    event = Event(
        type="auth",
        severity="info",
        message=f"New user registered: {db_user.username}",
        user_id=db_user.id,
        details={"email": db_user.email}
    )
    db.add(event)
    db.commit()
    
    logger.info(f"New user registered: {db_user.username} ({db_user.email})")
    return db_user

@app.post("/api/auth/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login user and return JWT token"""
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        # Log failed login attempt
        event = Event(
            type="auth",
            severity="warning",
            message=f"Failed login attempt for username: {form_data.username}",
            details={"username": form_data.username}
        )
        db.add(event)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Log successful login
    event = Event(
        type="auth",
        severity="info",
        message=f"User logged in: {user.username}",
        user_id=user.id,
        details={"username": user.username}
    )
    db.add(event)
    db.commit()
    
    logger.info(f"User logged in: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return current_user

@app.post("/api/auth/logout")
async def logout_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout user (client should delete token)"""
    # Log logout event
    event = Event(
        type="auth",
        severity="info",
        message=f"User logged out: {current_user.username}",
        user_id=current_user.id
    )
    db.add(event)
    db.commit()
    
    logger.info(f"User logged out: {current_user.username}")
    return {"message": "Successfully logged out"}

# ==================== MONITORING API ENDPOINTS ====================

@app.get("/api/metrics/host")
async def get_host_metrics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current host system metrics"""
    metrics = system_monitor.get_host_metrics()
    
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect host metrics"
        )
    
    return metrics

@app.get("/api/metrics/host/history")
async def get_host_metrics_history(
    metric_name: str,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get historical host metrics"""
    metrics = system_monitor.get_historical_metrics(db, metric_name, vm_id=None, limit=limit)
    
    return {
        "metric_name": metric_name,
        "count": len(metrics),
        "data": [
            {
                "value": m.value,
                "unit": m.unit,
                "timestamp": m.timestamp.isoformat()
            }
            for m in metrics
        ]
    }

@app.get("/api/metrics/vm/{vm_id}")
async def get_vm_metrics(
    vm_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current VM metrics"""
    vm = db.query(VM).filter(VM.id == vm_id).first()
    
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
    
    metrics = system_monitor.get_vm_metrics(vm)
    
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect VM metrics"
        )
    
    return metrics

@app.get("/api/metrics/vm/{vm_id}/history")
async def get_vm_metrics_history(
    vm_id: int,
    metric_name: str,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get historical VM metrics"""
    vm = db.query(VM).filter(VM.id == vm_id).first()
    
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
    
    metrics = system_monitor.get_historical_metrics(db, metric_name, vm_id=vm_id, limit=limit)
    
    return {
        "vm_id": vm_id,
        "metric_name": metric_name,
        "count": len(metrics),
        "data": [
            {
                "value": m.value,
                "unit": m.unit,
                "timestamp": m.timestamp.isoformat()
            }
            for m in metrics
        ]
    }

@app.post("/api/metrics/collect")
async def collect_metrics(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin: Manually trigger metric collection and storage"""
    metrics, alerts = system_monitor.collect_and_store_all_metrics(db)
    
    return {
        "success": True,
        "metrics": metrics,
        "alerts": alerts,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.delete("/api/metrics/cleanup")
async def cleanup_old_metrics(
    days: int = 7,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin: Clean up old metrics"""
    deleted = system_monitor.cleanup_old_metrics(db, days_to_keep=days)
    
    return {
        "success": True,
        "deleted_count": deleted,
        "days_kept": days
    }

@app.get("/api/metrics/alerts")
async def get_resource_alerts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current resource usage alerts"""
    metrics = system_monitor.get_host_metrics()
    alerts = system_monitor.check_resource_thresholds(db, metrics)
    
    return {
        "alerts": alerts,
        "count": len(alerts),
        "timestamp": datetime.utcnow().isoformat()
    }

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

# ==================== ADMIN USER MANAGEMENT ENDPOINTS ====================

@app.get("/api/admin/users", response_model=List[UserResponse])
async def admin_list_all_users(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin: List all users"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users

@app.get("/api/admin/users/{user_id}", response_model=UserResponse)
async def admin_get_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin: Get specific user details"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@app.patch("/api/admin/users/{user_id}", response_model=UserResponse)
async def admin_update_user(
    user_id: int,
    is_active: Optional[bool] = Body(None),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin: Update user status (activate/deactivate)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own account status"
        )
    
    if is_active is not None:
        user.is_active = is_active
        
        # Log the action
        event = Event(
            type="admin",
            severity="warning",
            message=f"Admin '{current_user.username}' {'activated' if is_active else 'deactivated'} user '{user.username}'",
            user_id=current_user.id,
            details={"target_user_id": user.id, "target_username": user.username, "is_active": is_active}
        )
        db.add(event)
    
    db.commit()
    db.refresh(user)
    return user

@app.post("/api/admin/users/{user_id}/credits")
async def admin_adjust_credits(
    user_id: int,
    amount: int = Body(..., ge=-10000, le=10000),
    reason: Optional[str] = Body(None),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin: Adjust user credits"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    old_credits = user.credits
    user.credits += amount
    
    # Ensure credits don't go negative
    if user.credits < 0:
        user.credits = 0
    
    # Log the action
    event = Event(
        type="admin",
        severity="info",
        message=f"Admin '{current_user.username}' adjusted credits for user '{user.username}': {old_credits} -> {user.credits} ({amount:+d})",
        user_id=current_user.id,
        details={
            "target_user_id": user.id,
            "target_username": user.username,
            "old_credits": old_credits,
            "new_credits": user.credits,
            "adjustment": amount,
            "reason": reason
        }
    )
    db.add(event)
    db.commit()
    db.refresh(user)
    
    return {
        "success": True,
        "user_id": user.id,
        "username": user.username,
        "old_credits": old_credits,
        "new_credits": user.credits,
        "adjustment": amount
    }

@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin: Delete a user and their VMs"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    username = user.username
    
    # Delete all user's VMs first
    user_vms = db.query(VM).filter(VM.owner_id == user_id).all()
    for vm in user_vms:
        vm_manager.destroy_vm(db, vm, user)
    
    # Log the action
    event = Event(
        type="admin",
        severity="critical",
        message=f"Admin '{current_user.username}' deleted user '{username}' and {len(user_vms)} VMs",
        user_id=current_user.id,
        details={"deleted_user_id": user_id, "deleted_username": username, "deleted_vms": len(user_vms)}
    )
    db.add(event)
    
    # Delete the user
    db.delete(user)
    db.commit()
    
    return {
        "success": True,
        "message": f"User '{username}' and {len(user_vms)} VMs deleted successfully"
    }

@app.get("/api/admin/statistics")
async def admin_get_statistics(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin: Get overall system statistics"""
    
    # User statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    admin_users = db.query(User).filter(User.is_admin == True).count()
    
    # VM statistics
    total_vms = db.query(VM).count()
    running_vms = db.query(VM).filter(VM.status == "running").count()
    stopped_vms = db.query(VM).filter(VM.status == "stopped").count()
    pending_vms = db.query(VM).filter(VM.status == "pending").count()
    error_vms = db.query(VM).filter(VM.status == "error").count()
    
    # Resource allocation statistics
    total_ram_allocated = db.query(VM).filter(VM.status.in_(["running", "stopped"])).with_entities(
        db.func.sum(VM.ram_mb)
    ).scalar() or 0
    total_disk_allocated = db.query(VM).filter(VM.status.in_(["running", "stopped"])).with_entities(
        db.func.sum(VM.disk_gb)
    ).scalar() or 0
    total_cpu_allocated = db.query(VM).filter(VM.status.in_(["running", "stopped"])).with_entities(
        db.func.sum(VM.cpu_cores)
    ).scalar() or 0
    
    # Event statistics (last 24 hours)
    from datetime import datetime, timedelta
    last_24h = datetime.utcnow() - timedelta(hours=24)
    events_24h = db.query(Event).filter(Event.created_at >= last_24h).count()
    critical_events_24h = db.query(Event).filter(
        Event.created_at >= last_24h,
        Event.severity == "critical"
    ).count()
    warning_events_24h = db.query(Event).filter(
        Event.created_at >= last_24h,
        Event.severity == "warning"
    ).count()
    
    # Host system metrics
    host_metrics = system_monitor.get_host_metrics()
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "admins": admin_users,
            "inactive": total_users - active_users
        },
        "vms": {
            "total": total_vms,
            "running": running_vms,
            "stopped": stopped_vms,
            "pending": pending_vms,
            "error": error_vms
        },
        "resources": {
            "ram_mb": total_ram_allocated,
            "ram_gb": round(total_ram_allocated / 1024, 2),
            "disk_gb": total_disk_allocated,
            "cpu_cores": total_cpu_allocated
        },
        "events": {
            "last_24h": events_24h,
            "critical": critical_events_24h,
            "warnings": warning_events_24h,
            "info": events_24h - critical_events_24h - warning_events_24h
        },
        "host": host_metrics,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/admin/emergency-stop-all")
async def admin_emergency_stop_all_vms(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin: Emergency stop all running VMs"""
    running_vms = db.query(VM).filter(VM.status == "running").all()
    
    stopped_count = 0
    failed_count = 0
    results = []
    
    for vm in running_vms:
        owner = db.query(User).filter(User.id == vm.owner_id).first()
        if owner:
            success, message = vm_manager.stop_vm(db, vm, owner)
            if success:
                stopped_count += 1
            else:
                failed_count += 1
            results.append({
                "vm_id": vm.id,
                "vm_name": vm.name,
                "owner": owner.username,
                "success": success,
                "message": message
            })
    
    # Log the emergency action
    event = Event(
        type="admin",
        severity="critical",
        message=f"Admin '{current_user.username}' executed emergency stop on all VMs: {stopped_count} stopped, {failed_count} failed",
        user_id=current_user.id,
        details={"stopped": stopped_count, "failed": failed_count, "results": results}
    )
    db.add(event)
    db.commit()
    
    return {
        "success": True,
        "stopped": stopped_count,
        "failed": failed_count,
        "total": len(running_vms),
        "results": results
    }

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

# ==================== SOC ENDPOINTS ====================

@app.get("/api/soc/events")
async def get_soc_events(
    limit: int = 50,
    event_type: str = None,
    severity: str = None,
    hours: int = 24,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get recent events with optional filtering"""
    events = soc_manager.get_recent_events(
        db=db,
        limit=limit,
        event_type=event_type,
        severity=severity,
        user_id=current_user.id if not current_user.is_admin else None,
        hours=hours
    )
    
    return [
        {
            "id": e.id,
            "type": e.type,
            "severity": e.severity,
            "message": e.message,
            "details": e.details,
            "user_id": e.user_id,
            "vm_id": e.vm_id,
            "created_at": e.created_at.isoformat()
        }
        for e in events
    ]

@app.get("/api/soc/statistics")
async def get_soc_statistics(
    hours: int = 24,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get event statistics for SOC dashboard"""
    stats = soc_manager.get_event_statistics(db=db, hours=hours)
    return stats

@app.get("/api/soc/user-activity/{user_id}")
async def get_user_activity(
    user_id: int,
    hours: int = 24,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin: Analyze user activity"""
    activity = soc_manager.analyze_user_activity(db=db, user_id=user_id, hours=hours)
    return activity

@app.post("/api/soc/ssh-attempt")
async def log_ssh_attempt(
    vm_id: int,
    success: bool,
    username: str,
    ip_address: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Log an SSH login attempt"""
    vm = db.query(VM).filter(VM.id == vm_id).first()
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VM not found"
        )
    
    # Check if user owns the VM or is admin
    if vm.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to log SSH attempts for this VM"
        )
    
    event = soc_manager.log_ssh_attempt(
        db=db,
        vm_id=vm_id,
        success=success,
        username=username,
        ip_address=ip_address
    )
    
    # Check for brute force attack
    is_attack, failed_count = soc_manager.detect_brute_force(db=db, vm_id=vm_id)
    
    return {
        "event_id": event.id if event else None,
        "success": success,
        "brute_force_detected": is_attack,
        "failed_attempts": failed_count
    }

@app.get("/api/soc/brute-force-check/{vm_id}")
async def check_brute_force(
    vm_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Check if a VM is under brute force attack"""
    vm = db.query(VM).filter(VM.id == vm_id).first()
    if not vm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="VM not found"
        )
    
    # Check if user owns the VM or is admin
    if vm.owner_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to check this VM"
        )
    
    is_attack, failed_count = soc_manager.detect_brute_force(db=db, vm_id=vm_id)
    
    return {
        "vm_id": vm_id,
        "vm_name": vm.name,
        "brute_force_detected": is_attack,
        "failed_attempts": failed_count
    }

@app.get("/api/admin/soc/all-events")
async def admin_get_all_soc_events(
    limit: int = 100,
    event_type: str = None,
    severity: str = None,
    hours: int = 24,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin: Get all SOC events with filtering"""
    events = soc_manager.get_recent_events(
        db=db,
        limit=limit,
        event_type=event_type,
        severity=severity,
        hours=hours
    )
    
    return [
        {
            "id": e.id,
            "type": e.type,
            "severity": e.severity,
            "message": e.message,
            "details": e.details,
            "user_id": e.user_id,
            "vm_id": e.vm_id,
            "created_at": e.created_at.isoformat(),
            "user": e.user.username if e.user else None,
            "vm_name": e.vm.name if e.vm else None
        }
        for e in events
    ]

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )