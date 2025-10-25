# 🔧 Developer Guide - Twarga Cloud

This guide provides technical documentation for developers who want to understand, modify, or extend Twarga Cloud.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Development Setup](#development-setup)
- [Core Components](#core-components)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Frontend Architecture](#frontend-architecture)
- [Testing](#testing)
- [Contributing](#contributing)
- [Best Practices](#best-practices)

---

## Architecture Overview

Twarga Cloud follows a modular, layered architecture:

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│    (Jinja2 Templates + HTMX/Alpine)    │
└──────────────────┬──────────────────────┘
                   │ HTTP/REST
┌──────────────────┴──────────────────────┐
│         Application Layer               │
│          (FastAPI Routes)               │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────┴──────────────────────┐
│          Business Logic Layer           │
│  ┌────────┬────────┬────────┬────────┐ │
│  │VM Mgr  │Monitor │  SOC   │Terminal│ │
│  │        │        │        │Manager │ │
│  └────────┴────────┴────────┴────────┘ │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────┴──────────────────────┐
│          Data Access Layer              │
│    (SQLAlchemy ORM + Database)         │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────┴──────────────────────┐
│        Infrastructure Layer             │
│   (Vagrant/KVM + ttyd + File System)   │
└─────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Dependency Injection**: Database sessions and dependencies injected via FastAPI
3. **Async First**: Use async/await for I/O operations
4. **Type Safety**: Pydantic models for validation and type checking
5. **Event-Driven**: All significant actions logged to the event system

---

## Project Structure

```
twarga-cloud/
├── backend/                    # Backend Python code
│   ├── main.py                # FastAPI app and routes (1,200 lines)
│   ├── auth.py                # Authentication logic (110 lines)
│   ├── models.py              # SQLAlchemy ORM models (160 lines)
│   ├── schemas.py             # Pydantic schemas (120 lines)
│   ├── database.py            # DB connection and setup (180 lines)
│   ├── vm_manager.py          # VM lifecycle management (780 lines)
│   ├── monitor.py             # System monitoring (580 lines)
│   ├── soc.py                 # Security event logging (600 lines)
│   ├── terminal.py            # Web terminal management (450 lines)
│   ├── migrations.py          # Database migrations (240 lines)
│   └── utils.py               # Shared utilities (50 lines)
│
├── frontend/                  # Frontend templates and assets
│   ├── templates/             # Jinja2 HTML templates
│   │   ├── base.html         # Base template with layout
│   │   ├── login.html        # Login page
│   │   ├── register.html     # Registration page
│   │   ├── dashboard.html    # User dashboard (1,500 lines)
│   │   ├── admin.html        # Admin panel (1,300 lines)
│   │   ├── monitor.html      # Monitoring dashboard (700 lines)
│   │   └── soc.html          # SOC event feed (800 lines)
│   └── static/
│       └── style.css         # Custom CSS (optional)
│
├── vms/                       # VM storage directory
├── logs/                      # Application logs
├── tests/                     # Test files
│   ├── test_db.py
│   ├── test_auth.py
│   ├── test_vm_manager.py
│   ├── test_monitor.py
│   └── test_soc.py
│
├── requirements.txt           # Python dependencies
├── setup.py                   # Setup script
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
└── README.md                 # Project documentation
```

---

## Development Setup

### Prerequisites

- Python 3.11+
- Vagrant 2.2+
- KVM/libvirt
- ttyd (optional)

### Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/twarga-cloud.git
cd twarga-cloud

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install black flake8 mypy pytest pytest-asyncio

# Initialize database
python -c "from backend.database import init_db; init_db()"

# Run tests
pytest
```

### Development Workflow

```bash
# Start development server with auto-reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, run tests on file changes
pytest-watch

# Format code
black backend/ frontend/

# Lint code
flake8 backend/

# Type checking
mypy backend/
```

### Environment Variables

Create a `.env` file:

```ini
# Development settings
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///./twarga_cloud.db

# Feature flags
ENABLE_TERMINAL=True
ENABLE_MONITORING=True
ENABLE_SOC=True

# Resource limits
MAX_VMS_PER_USER=5
MAX_TOTAL_RAM=8192
```

---

## Core Components

### 1. Authentication (`auth.py`)

Handles user authentication and JWT token management.

**Key Functions:**

```python
def verify_password(plain_password: str, hashed_password: str) -> bool
    """Verify a password against its hash"""

def get_password_hash(password: str) -> str
    """Hash a password using bcrypt"""

def create_access_token(data: dict, expires_delta: timedelta = None) -> str
    """Create a JWT access token"""

def get_current_user(token: str, db: Session) -> User
    """Get current user from JWT token"""

def get_current_active_user(current_user: User) -> User
    """Ensure user is active"""

def get_current_admin_user(current_user: User) -> User
    """Ensure user is admin"""
```

**Usage Example:**

```python
from backend.auth import get_password_hash, verify_password

# Hash a password
hashed = get_password_hash("mypassword")

# Verify password
is_valid = verify_password("mypassword", hashed)
```

### 2. VM Manager (`vm_manager.py`)

Manages VM lifecycle using Vagrant.

**Key Classes and Methods:**

```python
class VMManager:
    """Manages VM lifecycle operations"""
    
    def __init__(self, base_dir: str = "./vms", db_session=None):
        """Initialize VM manager"""
    
    async def create_vm(self, user_id: int, name: str, os_type: str, 
                       ram: int, cpu: int, disk: int) -> Dict:
        """Create a new VM with specified resources"""
    
    async def start_vm(self, user_id: int, vm_name: str) -> Dict:
        """Start a stopped VM"""
    
    async def stop_vm(self, user_id: int, vm_name: str) -> Dict:
        """Stop a running VM"""
    
    async def destroy_vm(self, user_id: int, vm_name: str) -> Dict:
        """Permanently destroy a VM"""
    
    def get_vm_status(self, user_id: int, vm_name: str) -> str:
        """Get current VM status from Vagrant"""
    
    def get_vm_ip(self, user_id: int, vm_name: str) -> str:
        """Get VM IP address from Vagrant"""
```

**VM Directory Structure:**

```
vms/user{id}-{vmname}/
├── Vagrantfile           # Generated Vagrant configuration
├── .vm_info              # JSON metadata file
└── .vagrant/             # Vagrant state directory
```

**VM Info JSON Format:**

```json
{
    "name": "test-vm",
    "user_id": 1,
    "os_type": "ubuntu/focal64",
    "ram": 1024,
    "cpu": 2,
    "disk": 20,
    "status": "running",
    "ip": "192.168.121.45",
    "created_at": "2025-01-15T10:30:00",
    "uptime": 3600
}
```

### 3. System Monitor (`monitor.py`)

Collects and stores system and VM metrics.

**Key Classes and Methods:**

```python
class SystemMonitor:
    """Monitors system and VM resources"""
    
    def __init__(self, db_session=None):
        """Initialize system monitor"""
    
    def get_host_metrics(self) -> Dict:
        """Get current host system metrics"""
    
    def get_vm_metrics(self, vm_id: int) -> Dict:
        """Get metrics for a specific VM"""
    
    async def store_host_metrics(self):
        """Store host metrics to database"""
    
    async def store_vm_metrics(self, vm_id: int):
        """Store VM metrics to database"""
    
    def check_resource_thresholds(self) -> List[Dict]:
        """Check for resource threshold violations"""
    
    def get_historical_metrics(self, metric_type: str, 
                              hours: int = 24) -> List[Dict]:
        """Get historical metrics"""
```

**Collected Metrics:**

- **CPU**: Usage %, core count, frequency
- **Memory**: Usage %, used/total/available MB, swap usage
- **Disk**: Usage %, used/total/free GB, I/O stats
- **Network**: Bytes sent/received, speed Mbps

**Metric Storage:**

Metrics are stored in the `metrics` table with:
- Timestamp
- Metric type (cpu, memory, disk, network)
- Entity (host or vm_id)
- Value (JSON with detailed metrics)

### 4. SOC Manager (`soc.py`)

Security event logging and analysis.

**Key Classes and Methods:**

```python
class SOCManager:
    """Security Operations Center event management"""
    
    def __init__(self, db_session=None):
        """Initialize SOC manager"""
    
    def log_event(self, event_type: str, message: str, 
                 severity: str = "info", **kwargs):
        """Log a security event"""
    
    def log_vm_created(self, vm_id: int, user_id: int, vm_name: str):
        """Log VM creation event"""
    
    def log_ssh_attempt(self, vm_id: int, username: str, 
                       success: bool, ip: str):
        """Log SSH login attempt"""
    
    def detect_brute_force(self, vm_id: int, minutes: int = 10) -> bool:
        """Detect SSH brute force attempts"""
    
    def get_recent_events(self, limit: int = 100, 
                         severity: str = None) -> List[Event]:
        """Get recent security events"""
    
    def get_event_statistics(self) -> Dict:
        """Get event statistics"""
```

**Event Types:**

- `vm`: VM lifecycle events
- `auth`: Authentication events
- `system`: System-level events
- `security`: Security incidents

**Severity Levels:**

- `info`: Normal operations
- `warning`: Potential issues
- `critical`: Security threats

### 5. Terminal Manager (`terminal.py`)

Web-based terminal session management.

**Key Classes and Methods:**

```python
class TerminalManager:
    """Manages web terminal sessions using ttyd"""
    
    def __init__(self, base_port: int = 7681, db_session=None):
        """Initialize terminal manager"""
    
    async def start_terminal_session(self, vm_id: int, 
                                     user_id: int) -> Dict:
        """Start a new terminal session for a VM"""
    
    async def stop_terminal_session(self, vm_id: int, user_id: int):
        """Stop an active terminal session"""
    
    def get_terminal_session(self, vm_id: int) -> Optional[Dict]:
        """Get active terminal session info"""
    
    async def cleanup_expired_sessions(self):
        """Clean up expired terminal sessions"""
    
    def verify_session_access(self, vm_id: int, user_id: int) -> bool:
        """Verify user can access terminal session"""
```

**Terminal Session Flow:**

1. User clicks "Terminal" button
2. Frontend calls `POST /api/terminal/start/{vm_id}`
3. Backend starts ttyd process with unique port
4. Returns session URL with authentication token
5. Frontend embeds ttyd in iframe
6. User interacts with terminal via WebSocket
7. Session expires after inactivity timeout
8. Backend cleans up expired sessions

---

## API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword"
}

Response: 201 Created
{
  "id": 1,
  "username": "newuser",
  "email": "user@example.com",
  "is_admin": false,
  "credits": 1000
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=testuser&password=testpass

Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### VM Management Endpoints

#### List VMs
```http
GET /api/vms
Authorization: Bearer {token}

Response: 200 OK
[
  {
    "id": 1,
    "name": "test-vm",
    "status": "running",
    "os_type": "ubuntu/focal64",
    "ram": 1024,
    "cpu": 2,
    "disk": 20,
    "ip_address": "192.168.121.45",
    "created_at": "2025-01-15T10:30:00"
  }
]
```

#### Create VM
```http
POST /api/vms
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "my-vm",
  "os_type": "ubuntu/focal64",
  "ram": 2048,
  "cpu": 2,
  "disk": 30
}

Response: 201 Created
{
  "id": 2,
  "name": "my-vm",
  "status": "pending",
  "message": "VM creation started"
}
```

#### VM Action (Start/Stop/Restart/Destroy)
```http
POST /api/vms/{vm_id}/action
Authorization: Bearer {token}
Content-Type: application/json

{
  "action": "start"  // or "stop", "restart", "destroy"
}

Response: 200 OK
{
  "status": "success",
  "message": "VM started successfully"
}
```

### Monitoring Endpoints

#### Get Host Metrics
```http
GET /api/metrics/host
Authorization: Bearer {token}

Response: 200 OK
{
  "cpu": {
    "usage_percent": 45.2,
    "count": 8,
    "frequency": 2400
  },
  "memory": {
    "usage_percent": 62.5,
    "used_mb": 10240,
    "total_mb": 16384
  },
  "disk": {
    "usage_percent": 55.0,
    "used_gb": 220,
    "total_gb": 400
  },
  "network": {
    "bytes_sent": 1024000,
    "bytes_recv": 2048000,
    "speed_mbps": 12.5
  }
}
```

#### Get VM Metrics
```http
GET /api/metrics/vm/{vm_id}
Authorization: Bearer {token}

Response: 200 OK
{
  "vm_id": 1,
  "cpu_usage": 35.0,
  "memory_usage": 45.0,
  "disk_usage": 40.0,
  "uptime": 3600,
  "ip_address": "192.168.121.45"
}
```

### SOC Endpoints

#### Get Events
```http
GET /api/soc/events?limit=50&severity=warning
Authorization: Bearer {token}

Response: 200 OK
[
  {
    "id": 1,
    "type": "vm",
    "severity": "info",
    "message": "VM test-vm created",
    "timestamp": "2025-01-15T10:30:00",
    "user_id": 1,
    "vm_id": 1
  }
]
```

#### Get Statistics
```http
GET /api/soc/statistics
Authorization: Bearer {token}

Response: 200 OK
{
  "total_events": 150,
  "info_count": 120,
  "warning_count": 25,
  "critical_count": 5,
  "by_type": {
    "vm": 80,
    "auth": 40,
    "system": 20,
    "security": 10
  }
}
```

### Admin Endpoints

#### List All Users
```http
GET /api/admin/users
Authorization: Bearer {admin_token}

Response: 200 OK
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@twarga.local",
    "is_admin": true,
    "is_active": true,
    "credits": 10000,
    "vm_count": 3
  }
]
```

#### Adjust User Credits
```http
POST /api/admin/users/{user_id}/credits
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "amount": 500,
  "reason": "Monthly credit allocation"
}

Response: 200 OK
{
  "user_id": 1,
  "new_balance": 1500,
  "adjustment": 500
}
```

---

## Database Schema

### ER Diagram

```
┌─────────────┐         ┌─────────────┐
│    User     │         │     VM      │
├─────────────┤         ├─────────────┤
│ id (PK)     │────┐    │ id (PK)     │
│ username    │    │    │ name        │
│ email       │    └───<│ user_id(FK) │
│ password    │         │ status      │
│ is_admin    │         │ os_type     │
│ is_active   │         │ ram         │
│ credits     │         │ cpu         │
│ created_at  │         │ disk        │
└─────────────┘         │ ip_address  │
                        │ created_at  │
       │                └─────────────┘
       │                       │
       │                       │
       ├───────────────────────┼────────┐
       │                       │        │
       ▼                       ▼        ▼
┌─────────────┐         ┌─────────────┐
│    Event    │         │   Metric    │
├─────────────┤         ├─────────────┤
│ id (PK)     │         │ id (PK)     │
│ type        │         │ timestamp   │
│ severity    │         │ metric_type │
│ message     │         │ entity      │
│ timestamp   │         │ value(JSON) │
│ user_id(FK) │         │ vm_id (FK)  │
│ vm_id (FK)  │         └─────────────┘
│ details(JSON)│
└─────────────┘
```

### Table Definitions

#### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    credits INTEGER DEFAULT 1000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### VMs Table
```sql
CREATE TABLE vms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    os_type VARCHAR(50) NOT NULL,
    ram INTEGER NOT NULL,
    cpu INTEGER NOT NULL,
    disk INTEGER NOT NULL,
    ip_address VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (user_id, name)
);
```

#### Events Table
```sql
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type VARCHAR(20) NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    vm_id INTEGER,
    details TEXT,  -- JSON
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (vm_id) REFERENCES vms(id) ON DELETE SET NULL
);
```

#### Metrics Table
```sql
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metric_type VARCHAR(20) NOT NULL,
    entity VARCHAR(20) NOT NULL,  -- 'host' or 'vm'
    entity_id INTEGER,  -- vm_id if entity='vm'
    value TEXT NOT NULL,  -- JSON
    FOREIGN KEY (entity_id) REFERENCES vms(id) ON DELETE CASCADE
);
```

### Indexes

```sql
CREATE INDEX idx_vms_user_id ON vms(user_id);
CREATE INDEX idx_vms_status ON vms(status);
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_events_severity ON events(severity);
CREATE INDEX idx_events_type ON events(type);
CREATE INDEX idx_metrics_timestamp ON metrics(timestamp DESC);
CREATE INDEX idx_metrics_entity ON metrics(entity, entity_id);
```

---

## Frontend Architecture

### Technology Stack

- **Jinja2**: Server-side templating
- **Tailwind CSS**: Utility-first CSS framework
- **HTMX**: HTML-over-the-wire interactions
- **Alpine.js**: Lightweight JavaScript framework
- **Chart.js**: Interactive charts

### Template Hierarchy

```
base.html
├── login.html
├── register.html
├── dashboard.html
├── admin.html
├── monitor.html
└── soc.html
```

### Component Pattern

Templates use Alpine.js for reactive state management:

```html
<div x-data="dashboardData()">
  <!-- Component HTML -->
  <div x-show="loading">Loading...</div>
  <div x-show="!loading" x-for="vm in vms">
    <span x-text="vm.name"></span>
  </div>
</div>

<script>
function dashboardData() {
  return {
    vms: [],
    loading: true,
    
    init() {
      this.loadVMs();
    },
    
    async loadVMs() {
      const response = await fetch('/api/vms', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      this.vms = await response.json();
      this.loading = false;
    }
  }
}
</script>
```

### State Management

**Global State (localStorage):**
- JWT token
- Theme preference (light/dark)
- User preferences

**Component State (Alpine.js):**
- UI state (modals, loading, errors)
- Form data
- Fetched data (VMs, metrics, events)

### HTMX Usage

HTMX is used for simple interactions:

```html
<!-- Auto-refresh every 5 seconds -->
<div hx-get="/api/metrics/host" 
     hx-trigger="every 5s"
     hx-target="#metrics">
  Loading...
</div>

<!-- Form submission -->
<form hx-post="/api/vms" 
      hx-target="#vm-list"
      hx-swap="beforeend">
  <!-- Form fields -->
</form>
```

---

## Testing

### Test Structure

```
tests/
├── test_db.py          # Database and model tests
├── test_auth.py        # Authentication tests
├── test_vm_manager.py  # VM management tests
├── test_monitor.py     # Monitoring tests
└── test_soc.py         # SOC tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest test_db.py

# Run with coverage
pytest --cov=backend --cov-report=html

# Run with verbose output
pytest -v
```

### Writing Tests

Example test:

```python
import pytest
from backend.database import SessionLocal
from backend.models import User
from backend.auth import get_password_hash

@pytest.fixture
def db():
    """Create a test database session"""
    session = SessionLocal()
    yield session
    session.close()

def test_create_user(db):
    """Test user creation"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("password"),
        credits=1000
    )
    db.add(user)
    db.commit()
    
    # Verify user was created
    saved_user = db.query(User).filter(
        User.username == "testuser"
    ).first()
    
    assert saved_user is not None
    assert saved_user.email == "test@example.com"
    assert saved_user.credits == 1000
```

### Integration Tests

Test VM manager integration:

```python
import pytest
from backend.vm_manager import VMManager

@pytest.mark.asyncio
async def test_vm_lifecycle():
    """Test complete VM lifecycle"""
    vm_manager = VMManager()
    
    # Create VM
    result = await vm_manager.create_vm(
        user_id=1,
        name="test-vm",
        os_type="ubuntu/focal64",
        ram=512,
        cpu=1,
        disk=10
    )
    assert result["status"] == "success"
    
    # Start VM
    result = await vm_manager.start_vm(1, "test-vm")
    assert result["status"] == "success"
    
    # Stop VM
    result = await vm_manager.stop_vm(1, "test-vm")
    assert result["status"] == "success"
    
    # Destroy VM
    result = await vm_manager.destroy_vm(1, "test-vm")
    assert result["status"] == "success"
```

---

## Contributing

### Code Style

We follow PEP 8 with these conventions:

```python
# Imports
from typing import Optional, Dict, List
import asyncio

# Type hints
def function_name(param: str, optional: Optional[int] = None) -> Dict:
    """Docstring with description.
    
    Args:
        param: Description of param
        optional: Description of optional param
    
    Returns:
        Dictionary with results
    """
    return {"result": param}

# Constants
MAX_VMS = 5
DEFAULT_RAM = 1024

# Classes
class MyClass:
    """Class docstring"""
    
    def __init__(self, value: int):
        self.value = value
    
    def method(self) -> str:
        """Method docstring"""
        return str(self.value)
```

### Commit Messages

Follow conventional commits:

```
feat: add VM snapshot feature
fix: resolve memory leak in monitor
docs: update API documentation
test: add tests for terminal manager
refactor: simplify VM status checking
perf: optimize metric collection
chore: update dependencies
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run tests and linters
6. Update documentation
7. Submit pull request
8. Address review comments

---

## Best Practices

### Error Handling

Always handle errors gracefully:

```python
from fastapi import HTTPException

try:
    result = await vm_manager.create_vm(...)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result
except Exception as e:
    logger.error(f"VM creation failed: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Logging

Use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

# Different log levels
logger.debug("Detailed information for debugging")
logger.info("General information about program execution")
logger.warning("Warning about potential issues")
logger.error("Error that occurred but program continues")
logger.critical("Critical error that may stop program")

# Include context
logger.info(f"VM {vm_name} created by user {user_id}")
```

### Database Sessions

Always use context managers:

```python
from backend.database import SessionLocal

def get_user(user_id: int):
    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()
        return user
```

Or use FastAPI dependencies:

```python
from fastapi import Depends
from backend.database import get_db

@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    return db.query(User).filter(User.id == user_id).first()
```

### Async Operations

Use async for I/O operations:

```python
import asyncio

async def process_vms(vm_ids: List[int]):
    # Run tasks concurrently
    tasks = [get_vm_metrics(vm_id) for vm_id in vm_ids]
    results = await asyncio.gather(*tasks)
    return results
```

---

## Performance Optimization

### Database Queries

Use eager loading to avoid N+1 queries:

```python
from sqlalchemy.orm import joinedload

# Bad - N+1 queries
users = db.query(User).all()
for user in users:
    print(user.vms)  # Separate query for each user

# Good - Single query with join
users = db.query(User).options(joinedload(User.vms)).all()
for user in users:
    print(user.vms)  # No additional queries
```

### Caching

Implement caching for frequently accessed data:

```python
from functools import lru_cache
from datetime import datetime, timedelta

_cache = {}
_cache_timeout = {}

def cached_function(key: str, timeout: int = 60):
    def decorator(func):
        def wrapper(*args, **kwargs):
            now = datetime.now()
            if key in _cache and _cache_timeout.get(key, now) > now:
                return _cache[key]
            
            result = func(*args, **kwargs)
            _cache[key] = result
            _cache_timeout[key] = now + timedelta(seconds=timeout)
            return result
        return wrapper
    return decorator

@cached_function("host_metrics", timeout=5)
def get_host_metrics():
    # Expensive operation
    return collect_metrics()
```

### Async Background Tasks

Use FastAPI's BackgroundTasks for async operations:

```python
from fastapi import BackgroundTasks

def cleanup_old_metrics(days: int):
    # Long-running cleanup task
    pass

@app.post("/api/cleanup")
def trigger_cleanup(background_tasks: BackgroundTasks):
    background_tasks.add_task(cleanup_old_metrics, days=7)
    return {"status": "cleanup started"}
```

---

## Security Considerations

### Input Validation

Always validate user input:

```python
from pydantic import BaseModel, validator

class VMCreate(BaseModel):
    name: str
    ram: int
    cpu: int
    disk: int
    
    @validator('name')
    def validate_name(cls, v):
        if not v.islower() or ' ' in v:
            raise ValueError('Name must be lowercase without spaces')
        return v
    
    @validator('ram')
    def validate_ram(cls, v):
        if v < 512 or v > 4096:
            raise ValueError('RAM must be between 512 and 4096 MB')
        return v
```

### Authentication

Protect routes with authentication:

```python
from backend.auth import get_current_user, get_current_admin_user

@app.get("/api/vms")
def list_vms(current_user: User = Depends(get_current_user)):
    # Only authenticated users can access
    return get_user_vms(current_user.id)

@app.get("/api/admin/users")
def list_users(admin: User = Depends(get_current_admin_user)):
    # Only admins can access
    return get_all_users()
```

### SQL Injection Prevention

Use ORM queries, not raw SQL:

```python
# Bad - SQL injection risk
db.execute(f"SELECT * FROM users WHERE username = '{username}'")

# Good - Parameterized query
db.query(User).filter(User.username == username).first()
```

---

## Deployment

### Production Checklist

- [ ] Change SECRET_KEY in .env
- [ ] Set DEBUG=False
- [ ] Use production database (PostgreSQL/MySQL)
- [ ] Enable HTTPS with reverse proxy
- [ ] Configure firewall rules
- [ ] Set up log rotation
- [ ] Implement database backups
- [ ] Configure monitoring and alerts
- [ ] Set resource limits
- [ ] Review security headers

### Docker Deployment (Future)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "backend.main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

---

**Questions?** Open an issue on GitHub or check the [troubleshooting guide](TROUBLESHOOTING.md).
