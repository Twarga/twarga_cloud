# 🧁 LabsBakery Core

**Build cyber labs like designing slides**

LabsBakery is a visual lab builder that lets cybersecurity instructors create and share virtual lab environments with students. Think Canva for cyber labs.

## 🎯 What is LabsBakery?

LabsBakery transforms the complex process of creating cybersecurity lab environments into a simple, visual experience:

- **For Teachers:** Drag-and-drop VM nodes, connect networks, write tutorials, export as a single `.labpkg` file
- **For Students:** Import `.labpkg`, click "Bake Lab", VMs start automatically, follow built-in tutorials

## ✨ Features (MVP - Phase 1)

### Core Functionality
- ✅ **Visual Canvas Builder** - Drag and drop VM nodes
- ✅ **Project Management** - Create, save, and organize labs
- ✅ **Export/Import System** - Share labs as `.labpkg` files
- ✅ **Schema Validation** - Ensure lab compatibility
- ✅ **Database Models** - Projects, VMs, Networks, Tutorials

### Coming Soon (Phases 2-8)
- 🔄 VM Runtime (Vagrant integration)
- 🔄 Terminal Access (SSH in browser)
- 🔄 Desktop Access (VNC in browser)
- 🔄 Tutorial System (Step-by-step guides)
- 🔄 Monitoring & Metrics
- 🔄 Provider Adapters (libvirt, Hyper-V)

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- (Optional) Vagrant + libvirt or Hyper-V for running VMs

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd labsbakery
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment:**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Initialize database:**
```bash
python -c "from backend.database import init_db; init_db()"
```

6. **Run the application:**
```bash
uvicorn backend.main:app --reload
```

7. **Open your browser:**
```
http://localhost:8000
```

## 📦 Project Structure

```
labsbakery/
├── backend/
│   ├── models/           # Database models (Project, VM, Tutorial)
│   ├── routes/           # API routes (projects, runtime, terminal)
│   ├── services/         # Business logic (export, import, validation)
│   ├── adapters/         # Provider adapters (libvirt, Hyper-V)
│   ├── utils/            # Utilities (schema validator, preflight checks)
│   ├── config.py         # Configuration management
│   ├── database.py       # Database setup
│   └── main.py           # FastAPI application
├── frontend/
│   ├── templates/        # Jinja2 HTML templates
│   └── static/           # CSS, JS, assets
├── lab_schema.json       # JSON schema for lab packages
├── requirements.txt      # Python dependencies
└── README.md
```

## 🔌 API Endpoints

### Projects
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details
- `PATCH /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project
- `GET /api/projects/{id}/stats` - Get project statistics

### Export/Import
- `POST /api/projects/{id}/export` - Export project as `.labpkg`
- `POST /api/projects/import` - Import `.labpkg` file
- `POST /api/projects/validate` - Validate `.labpkg` file

### Utilities
- `GET /health` - Health check
- `GET /api` - API information
- `GET /docs` - Interactive API documentation (Swagger)

## 📚 Usage Examples

### Create a New Lab

1. Open LabsBakery in your browser
2. Click **"New Lab"** (TODO: implement button)
3. Drag VM nodes onto the canvas
4. Click each node to configure RAM, CPU, network
5. Click **"Save"** to save your project

### Export a Lab

```bash
curl -X POST http://localhost:8000/api/projects/1/export \
  -o MyLab.labpkg
```

### Import a Lab

```bash
curl -X POST http://localhost:8000/api/projects/import \
  -F "file=@MyLab.labpkg"
```

### Validate a Lab

```bash
curl -X POST http://localhost:8000/api/projects/validate \
  -F "file=@MyLab.labpkg"
```

## 🧪 Lab Package Format

A `.labpkg` file is a ZIP containing:

```
MyLab.labpkg/
├── lab.json          # Lab configuration (VMs, networks, tutorial)
├── metadata.json     # Title, author, description
├── assets/           # Screenshots, videos, etc.
└── thumbnail.png     # Lab preview image
```

### lab.json Schema

```json
{
  "schemaVersion": 1,
  "metadata": {
    "title": "Web Pentesting 101",
    "author": "Prof. Ahmed",
    "description": "Learn SQL injection",
    "tags": ["web", "pentest", "beginner"]
  },
  "canvas": {
    "nodes": [...],
    "links": [...]
  },
  "ingredients": [
    {
      "id": "node_1",
      "name": "Kali Linux",
      "box": "kalilinux/rolling",
      "ram": 2048,
      "cpu": 2,
      "network": "net_1",
      "ip": "192.168.56.10"
    }
  ],
  "tutorial": {
    "steps": [...]
  }
}
```

## 🗺️ Development Roadmap

### ✅ Phase 1: Foundation (Week 1-2) - COMPLETE
- [x] Project setup and structure
- [x] Database models (Project, VM, Network, Tutorial)
- [x] Basic API routes (CRUD operations)
- [x] Schema validator
- [x] Export/Import system
- [x] Basic UI (canvas with node palette)

### 🔄 Phase 2: Provider Adapters (Week 3)
- [ ] Provider resolver (Linux/Windows detection)
- [ ] libvirt adapter (Linux)
- [ ] Hyper-V adapter (Windows)
- [ ] Vagrantfile generation

### 🔄 Phase 3: Preflight & Validation (Week 4)
- [ ] Resource checker (RAM, CPU, disk)
- [ ] Error mapping system
- [ ] Dependency validation

### 🔄 Phase 4: Canvas UX (Week 5)
- [ ] jsPlumb integration
- [ ] Drag-and-drop functionality
- [ ] Connection drawing
- [ ] Canvas state persistence

### 🔄 Phase 5: Terminal & VNC (Week 6)
- [ ] xterm.js terminal integration
- [ ] WebSocket SSH proxy
- [ ] noVNC desktop viewer
- [ ] Multi-VM session management

### 🔄 Phase 6: Tutorial System (Week 7)
- [ ] TipTap rich text editor
- [ ] Image upload
- [ ] Code blocks with syntax highlighting
- [ ] Progress tracking

### 🔄 Phase 7: Templates & Polish (Week 8)
- [ ] Built-in lab templates
- [ ] Installer scripts
- [ ] Documentation
- [ ] UI polish

### 🔄 Phase 8: Testing & Launch (Week 9-10)
- [ ] Integration tests
- [ ] User acceptance testing
- [ ] Performance optimization
- [ ] Launch preparation

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the amazing web framework
- Alpine.js for lightweight reactivity
- Tailwind CSS for rapid styling
- Vagrant for VM orchestration

## 📧 Contact

For questions, issues, or suggestions, please open an issue on GitHub.

---

**Built with ❤️ for cybersecurity education**
