# ☁️ Twarga Cloud MVP - Local Cloud Simulation Lab

<div align="center">

![Twarga Cloud](https://img.shields.io/badge/Twarga-Cloud-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-green?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal?style=for-the-badge&logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**A self-hosted mini IaaS platform for learning cloud operations, VM orchestration, and security monitoring**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Architecture](#-architecture) • [Screenshots](#-screenshots)

</div>

---

## 📖 Overview

**Twarga Cloud** is a local Infrastructure-as-a-Service (IaaS) simulator designed for educational purposes. It behaves like a small-scale version of Linode or DigitalOcean, allowing you to deploy virtual machines, monitor resources, and manage users - all on a single machine.

This project simulates:
- **Cloud Infrastructure**: Full VM lifecycle management with custom specs
- **Operations Monitoring**: Live system and per-VM resource tracking
- **Security Operations Center (SOC)**: Centralized event logging and security monitoring
- **Multi-tenancy**: User management with credit-based quota system

### 🎯 Educational Purpose

Perfect for learning:
- Cloud orchestration and VM lifecycle management
- Infrastructure monitoring and alerting systems
- Security event correlation and incident detection
- Building production-ready REST APIs with FastAPI
- Modern web UI with HTMX and Alpine.js

## ✨ Features

### 👤 User Features
- **User Authentication**: Secure JWT-based registration and login
- **VM Management**: Create, start, stop, restart, and destroy VMs with custom specs
- **Resource Selection**: Choose RAM (512MB-4GB), CPU cores (1-4), disk (10-50GB), and OS type
- **Web Terminal**: Direct SSH access to VMs via browser-embedded terminal
- **Credit System**: Manage virtual credits for resource allocation
- **Live Monitoring**: Real-time system and VM resource usage charts
- **Dark Mode**: Modern UI with light/dark theme support

### 👨‍💼 Admin Features
- **User Management**: View, activate/deactivate, and delete user accounts
- **Credit Control**: Adjust user credits with audit logging
- **Global VM Management**: Monitor and control all VMs across all users
- **SOC Dashboard**: Centralized security event feed with filtering
- **System Statistics**: Host-level resource usage and allocation tracking
- **Bulk Operations**: Perform actions on multiple users simultaneously

### 🛡️ Monitoring & Security
- **Host Monitoring**: CPU, memory, disk, network I/O tracking (5-second intervals)
- **VM Monitoring**: Per-VM resource usage with historical data
- **Event Logging**: Comprehensive logging of all system activities
- **SOC Feed**: Real-time security event display with severity classification
- **Alert System**: Automatic alerts for resource thresholds and suspicious activities
- **Brute Force Detection**: Automatic detection of failed SSH login attempts

### 🔧 Technical Features
- **FastAPI Backend**: High-performance async REST API
- **Vagrant Integration**: VM orchestration with KVM/libvirt
- **SQLite Database**: Lightweight persistence for users, VMs, and events
- **HTMX & Alpine.js**: Modern reactive frontend without heavy frameworks
- **Tailwind CSS**: Beautiful, responsive UI design
- **ttyd Integration**: Web-based terminal access to VMs

## 🚀 Quick Start

### Prerequisites

- **Operating System**: Linux (Ubuntu 20.04+ or Debian 11+ recommended)
- **Python**: 3.11 or higher
- **Vagrant**: 2.2.0 or higher
- **Virtualization**: KVM/QEMU with libvirt
- **ttyd**: For web terminal access (optional)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/twarga-cloud.git
cd twarga-cloud

# 2. Run the setup script
python3 setup.py

# 3. Activate the virtual environment
source venv/bin/activate

# 4. Start the application
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at: **http://localhost:8000**

### First Steps

1. **Register an account** at http://localhost:8000/register
2. **Login** with your credentials
3. **Launch your first VM** from the dashboard
4. **Access the terminal** when the VM is running
5. **Monitor resources** on the /monitor page
6. **View security events** on the /soc page

For detailed installation instructions, see [INSTALL.md](INSTALL.md).

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [INSTALL.md](INSTALL.md) | Complete installation and setup guide |
| [USER_GUIDE.md](USER_GUIDE.md) | User manual and feature documentation |
| [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) | Developer documentation and API reference |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Common issues and solutions |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
│              (HTMX + Alpine.js + Tailwind CSS)              │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │  Auth    │    VM    │ Monitor  │   SOC    │ Terminal │  │
│  │  Module  │  Manager │  Module  │  Module  │  Manager │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────┐   ┌──────────┐   ┌──────────┐
    │ SQLite  │   │  Vagrant │   │   ttyd   │
    │Database │   │   (KVM)  │   │(Terminal)│
    └─────────┘   └──────────┘   └──────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Virtual Machines│
              │  (Ubuntu/Debian/ │
              │    CentOS)       │
              └─────────────────┘
```

### Tech Stack

**Backend:**
- FastAPI 0.104+ - Modern Python web framework
- SQLAlchemy 2.0 - ORM for database operations
- psutil - System monitoring
- python-jose - JWT authentication
- passlib - Password hashing

**Frontend:**
- Jinja2 - Template engine
- Tailwind CSS - Utility-first CSS framework
- HTMX - HTML over the wire
- Alpine.js - Lightweight JavaScript framework
- Chart.js - Resource usage charts

**Infrastructure:**
- Vagrant - VM orchestration
- libvirt/KVM - Virtualization provider
- ttyd - Web terminal

## 📁 Project Structure

```
twarga-cloud/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── auth.py              # Authentication & JWT handling
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic validation schemas
│   ├── database.py          # Database connection & setup
│   ├── vm_manager.py        # VM lifecycle management
│   ├── monitor.py           # System & VM monitoring
│   ├── soc.py               # Security event logging
│   ├── terminal.py          # Web terminal management
│   ├── migrations.py        # Database migrations
│   └── utils.py             # Shared utilities
├── frontend/
│   ├── templates/           # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── dashboard.html
│   │   ├── admin.html
│   │   ├── monitor.html
│   │   └── soc.html
│   └── static/
│       └── style.css        # Custom CSS (if any)
├── vms/                     # User VM directories
│   └── user{id}-{vmname}/
│       ├── Vagrantfile
│       └── .vm_info
├── logs/                    # Application logs
│   ├── events.log
│   └── ssh_attempts.log
├── requirements.txt         # Python dependencies
├── setup.py                 # Setup script
├── .env.example             # Environment variables template
└── README.md                # This file
```

## 🎨 Screenshots

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)
*VM management dashboard with real-time status updates*

### Monitoring
![Monitoring](docs/screenshots/monitoring.png)
*Live system and VM resource monitoring with charts*

### SOC Feed
![SOC](docs/screenshots/soc.png)
*Security Operations Center with event filtering*

### Admin Panel
![Admin](docs/screenshots/admin.png)
*Administrative control panel for user and VM management*

## 🔌 API Reference

### Authentication Endpoints
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/logout` - Logout current user

### VM Management Endpoints
- `GET /api/vms` - List user's VMs
- `POST /api/vms` - Create new VM
- `GET /api/vms/{vm_id}` - Get VM details
- `POST /api/vms/{vm_id}/action` - Perform VM action (start/stop/restart/destroy)

### Monitoring Endpoints
- `GET /api/metrics/host` - Get host system metrics
- `GET /api/metrics/vm/{vm_id}` - Get VM metrics
- `GET /api/metrics/alerts` - Get active resource alerts

### SOC Endpoints
- `GET /api/soc/events` - Get security events
- `GET /api/soc/statistics` - Get event statistics
- `POST /api/soc/ssh-attempt` - Log SSH attempt

### Admin Endpoints
- `GET /api/admin/users` - List all users
- `PATCH /api/admin/users/{user_id}` - Update user
- `POST /api/admin/users/{user_id}/credits` - Adjust user credits
- `GET /api/admin/vms` - List all VMs
- `GET /api/admin/statistics` - Get system statistics

For complete API documentation, visit http://localhost:8000/docs after starting the application.

## 🧪 Testing

Run the test suite:

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run specific test files
python test_db.py          # Database tests
python test_auth.py        # Authentication tests
python test_vm_manager.py  # VM management tests
python test_monitor.py     # Monitoring tests
python test_soc.py         # SOC tests
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Vagrant for VM orchestration
- HTMX for modern HTML interactions
- Alpine.js for lightweight reactivity
- Tailwind CSS for beautiful styling

## 📞 Support

- **Documentation**: See the [docs](docs/) directory
- **Issues**: Report bugs on [GitHub Issues](https://github.com/yourusername/twarga-cloud/issues)
- **Discussions**: Join our [Discussions](https://github.com/yourusername/twarga-cloud/discussions)

## 🗺️ Roadmap

### Current Version: v0.1 (MVP)
- ✅ User authentication and management
- ✅ VM lifecycle management
- ✅ System and VM monitoring
- ✅ SOC event feed
- ✅ Admin dashboard
- ✅ Web terminal access

### Future Versions
- **v0.2**: Email alerts and notifications
- **v0.3**: Multi-node support with remote Proxmox
- **v0.4**: Docker container integration
- **v0.5**: SIEM export to Elastic/Splunk
- **v1.0**: Public demo and open-source release

---

<div align="center">

**Built with ❤️ for cloud and security enthusiasts**

[⬆ Back to Top](#️-twarga-cloud-mvp---local-cloud-simulation-lab)

</div>
