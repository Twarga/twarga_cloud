# 🧁 LABSBAKERY - PHASE 1 IMPLEMENTATION PLAN

## Overview
This document outlines the detailed implementation plan for Phase 1 (Foundation) of LabsBakery Core - a cyber lab builder that lets teachers and students create and run virtual lab environments.

## Phase 1: Foundation (Week 1-2) - 42 hours

### Task 1.1: Project Setup (4 hours) ✅
**What to do:**
1. Create repository structure for LabsBakery
2. Initialize Python project with virtual environment
3. Create directory structure
4. Initialize git for LabsBakery components

**Acceptance criteria:**
- ✅ Virtual environment activates
- ✅ Can run backend
- ✅ No import errors

**Directory Structure:**
```
labsbakery/
├── backend/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Settings, env vars
│   ├── database.py                # SQLModel setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── project.py             # Project, Lab models
│   │   ├── vm.py                  # VM, Network models
│   │   └── tutorial.py            # Tutorial, Step models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── projects.py            # CRUD for labs
│   │   ├── runtime.py             # Start/stop VMs
│   │   ├── terminal.py            # WebSocket SSH proxy
│   │   ├── vnc.py                 # WebSocket VNC proxy
│   │   └── templates.py           # Built-in lab templates
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract Provider class
│   │   ├── libvirt_adapter.py     # Linux provider
│   │   ├── hyperv_adapter.py      # Windows provider
│   │   └── resolver.py            # Auto-detect provider
│   ├── services/
│   │   ├── __init__.py
│   │   ├── vagrant_service.py     # Vagrant operations
│   │   ├── validation_service.py  # Preflight checks
│   │   ├── export_service.py      # Create .labpkg
│   │   └── import_service.py      # Load .labpkg
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── preflight.py           # System resource checks
│   │   ├── schema_validator.py    # JSON schema validation
│   │   ├── error_mapper.py        # Error code mapping
│   │   └── logger.py              # Logging setup
│   └── workers/
│       ├── __init__.py
│       └── job_queue.py           # Async VM operations
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── tailwind.min.css
│   │   ├── js/
│   │   │   ├── alpine.min.js
│   │   │   ├── jsplumb.min.js
│   │   │   ├── tiptap-bundle.js
│   │   │   ├── xterm.min.js
│   │   │   ├── novnc.min.js
│   │   │   ├── app.js              # Main app logic
│   │   │   ├── canvas.js           # Canvas interactions
│   │   │   ├── tutorial.js         # Tutorial editor
│   │   │   ├── terminal.js         # Terminal proxy
│   │   │   └── api.js              # API client
│   │   └── assets/
│   │       ├── icons/
│   │       └── templates/          # VM node templates
│   └── templates/
│       ├── base.html               # Base layout
│       ├── builder.html            # Main canvas view
│       ├── tutorial.html           # Tutorial editor
│       ├── terminal.html           # Terminal view
│       └── components/
│           ├── node.html           # VM node template
│           ├── modal.html          # Modal dialogs
│           └── notifications.html  # Toast notifications
├── lab_schema.json                 # JSON schema for lab packages
├── labsbakery.db                  # SQLite database
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

### Task 1.2: Database Models (6 hours)
**What to do:**
1. Create `backend/models/project.py` with Project model
2. Create `backend/models/vm.py` with VM and Network models
3. Create `backend/models/tutorial.py` with Tutorial and Step models
4. Create `backend/database.py` with SQLModel engine
5. Test database creation and CRUD operations

**Models to implement:**
- Project: id, title, description, author, created_at, updated_at, canvas_state, tutorial_content, status
- VM: id, project_id, name, box, ram_mb, cpu_cores, network_id, ip_address, ssh_port, vnc_port, status
- Network: id, project_id, name, subnet, dhcp_enabled

**Acceptance criteria:**
- ✅ Database file created: `labsbakery.db`
- ✅ Tables exist: `project`, `vm`, `network`
- ✅ Can insert/query records via SQLModel

### Task 1.3: Basic API Routes (8 hours)
**What to do:**
1. Create `backend/routes/projects.py` with CRUD endpoints
2. Implement GET /api/projects (list all)
3. Implement POST /api/projects (create new)
4. Implement GET /api/projects/{id} (get one)
5. Implement PATCH /api/projects/{id} (update)
6. Implement DELETE /api/projects/{id} (delete)
7. Create `backend/main.py` with FastAPI app
8. Test all endpoints with curl or HTTP client

**Endpoints:**
```
GET    /api/projects           - List all projects
POST   /api/projects           - Create new project
GET    /api/projects/{id}      - Get project details
PATCH  /api/projects/{id}      - Update project
DELETE /api/projects/{id}      - Delete project
```

**Acceptance criteria:**
- ✅ All CRUD operations work
- ✅ Returns proper HTTP status codes (200, 201, 404, etc.)
- ✅ JSON responses are valid

### Task 1.4: Schema Validator (6 hours)
**What to do:**
1. Create `lab_schema.json` with JSON schema definition
2. Create `backend/utils/schema_validator.py` with validation logic
3. Implement schema validation for lab packages
4. Add error messages for invalid schemas
5. Test with valid and invalid lab data

**Schema structure:**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["schemaVersion", "metadata", "canvas", "ingredients"],
  "properties": {
    "schemaVersion": {"type": "integer", "const": 1},
    "metadata": {
      "type": "object",
      "required": ["title", "author"],
      "properties": {
        "title": {"type": "string", "minLength": 1},
        "author": {"type": "string", "minLength": 1},
        "description": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}}
      }
    },
    "canvas": {
      "type": "object",
      "properties": {
        "nodes": {"type": "array"},
        "links": {"type": "array"}
      }
    },
    "ingredients": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name", "box"],
        "properties": {
          "id": {"type": "string"},
          "name": {"type": "string"},
          "box": {"type": "string"},
          "ram": {"type": "integer", "minimum": 512},
          "cpu": {"type": "integer", "minimum": 1}
        }
      }
    }
  }
}
```

**Acceptance criteria:**
- ✅ Valid labs pass validation
- ✅ Invalid labs return clear error messages
- ✅ Schema enforces required fields

### Task 1.5: Export/Import System (10 hours)
**What to do:**
1. Create `backend/services/export_service.py`
2. Implement lab export as .labpkg (ZIP file)
3. Create `backend/services/import_service.py`
4. Implement lab import from .labpkg
5. Add API endpoints for export/import
6. Test full export-import cycle

**Export format:**
```
WebPentest101.labpkg (ZIP file)
  ├── lab.json          # Canvas, VMs, networks, tutorial
  ├── metadata.json     # Title, author, description, version
  ├── assets/
  │   ├── screenshot1.png
  │   ├── screenshot2.png
  │   └── demo_video.mp4
  └── thumbnail.png     # Preview image
```

**Endpoints:**
```
POST /api/projects/{id}/export  - Export lab as .labpkg
POST /api/projects/import       - Import .labpkg file
```

**Acceptance criteria:**
- ✅ Can export project as .labpkg ZIP file
- ✅ ZIP contains lab.json + assets folder
- ✅ Can import .labpkg and recreate project
- ✅ Import validates schema before creating project

### Task 1.6: Basic UI (8 hours)
**What to do:**
1. Create `frontend/templates/base.html` with Tailwind CSS
2. Create `frontend/templates/builder.html` with canvas area
3. Add Alpine.js for reactive state management
4. Implement basic node palette
5. Add node creation functionality
6. Create properties panel
7. Test UI in browser

**UI Components:**
- Navigation bar with LabsBakery branding
- Left sidebar with VM palette (Kali, Ubuntu, Windows, etc.)
- Center canvas area for node placement
- Right sidebar for node properties
- Bottom status bar

**Acceptance criteria:**
- ✅ Can open http://localhost:8000 and see UI
- ✅ Can click "Kali Linux" and node appears on canvas
- ✅ Clicking node shows properties panel
- ✅ Can edit node name, RAM, CPU in properties

## Phase 1 Complete Checklist
- ✅ FastAPI server runs
- ✅ Database models created
- ✅ CRUD API works
- ✅ Schema validator works
- ✅ Export/import works
- ✅ Basic UI renders nodes

**Total Time:** 42 hours (~2 weeks at 20hrs/week)

## Next Steps (Phase 2)
After Phase 1 completion, move to Phase 2: Provider Adapters
- Task 2.1: Provider Resolver (4 hours)
- Task 2.2: libvirt Adapter for Linux (8 hours)
- Task 2.3: Hyper-V Adapter for Windows (8 hours)
