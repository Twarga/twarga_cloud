# 🚀 Installation Guide - Twarga Cloud

This guide will walk you through the installation and setup of Twarga Cloud on your local machine.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [System Requirements](#system-requirements)
- [Installation Steps](#installation-steps)
- [Configuration](#configuration)
- [Starting the Application](#starting-the-application)
- [Creating Admin Account](#creating-admin-account)
- [Verification](#verification)
- [Post-Installation](#post-installation)

---

## Prerequisites

Before installing Twarga Cloud, ensure you have the following installed on your system:

### Required Software

#### 1. Python 3.11+

```bash
# Check Python version
python3 --version

# Install Python 3.11+ on Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# Install Python 3.11+ on Fedora/RHEL
sudo dnf install python3.11 python3.11-devel
```

#### 2. Vagrant

```bash
# Check Vagrant version
vagrant --version

# Install Vagrant on Ubuntu/Debian
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install vagrant

# Or download from https://www.vagrantup.com/downloads
```

#### 3. KVM/QEMU with libvirt

```bash
# Check if KVM is supported
egrep -c '(vmx|svm)' /proc/cpuinfo
# If output is > 0, KVM is supported

# Install KVM and libvirt on Ubuntu/Debian
sudo apt install qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virt-manager

# Add your user to libvirt group
sudo usermod -aG libvirt $USER
sudo usermod -aG kvm $USER

# Start libvirt service
sudo systemctl enable libvirtd
sudo systemctl start libvirtd

# Verify installation
sudo virsh list --all
```

#### 4. Vagrant libvirt Plugin

```bash
# Install dependencies for libvirt plugin
sudo apt install build-essential libvirt-dev ruby-dev

# Install vagrant-libvirt plugin
vagrant plugin install vagrant-libvirt

# Verify plugin installation
vagrant plugin list
```

#### 5. ttyd (Optional - for web terminal)

```bash
# Install ttyd on Ubuntu/Debian
sudo apt install ttyd

# Or build from source
git clone https://github.com/tsl0922/ttyd.git
cd ttyd && mkdir build && cd build
cmake ..
make && sudo make install

# Verify installation
ttyd --version
```

---

## System Requirements

### Minimum Requirements
- **OS**: Linux (Ubuntu 20.04+, Debian 11+, or equivalent)
- **CPU**: 4 cores (x86_64 with VT-x/AMD-V support)
- **RAM**: 8 GB
- **Disk**: 50 GB free space
- **Network**: Internet connection for initial setup

### Recommended Requirements
- **CPU**: 8+ cores
- **RAM**: 16+ GB
- **Disk**: 100+ GB SSD
- **Network**: 1 Gbps connection

---

## Installation Steps

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/twarga-cloud.git

# Navigate to project directory
cd twarga-cloud
```

### Step 2: Run Setup Script

The setup script will automatically:
- Create a Python virtual environment
- Install all dependencies
- Set up the database
- Create necessary directories
- Generate configuration files

```bash
# Run setup script
python3 setup.py
```

You should see output like:
```
🚀 Twarga Cloud - Setup Script
================================

📦 Step 1/6: Creating virtual environment...
✅ Virtual environment created at: venv

📦 Step 2/6: Installing dependencies...
✅ Dependencies installed successfully

📦 Step 3/6: Setting up database...
✅ Database initialized successfully

📦 Step 4/6: Creating directories...
✅ Directories created: vms/, logs/

📦 Step 5/6: Generating configuration files...
✅ Configuration file created: .env

✅ Setup completed successfully!
```

### Step 3: Activate Virtual Environment

```bash
# On Linux/Mac
source venv/bin/activate

# Your prompt should change to show (venv)
```

### Step 4: Verify Installation

```bash
# Run database tests
python test_db.py

# Run authentication tests
python test_auth.py

# All tests should pass
```

---

## Configuration

### Environment Variables

Edit the `.env` file to customize your installation:

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

Key configuration options:

```ini
# Application Settings
APP_NAME=Twarga Cloud
APP_VERSION=0.1.0
DEBUG=True

# Security Settings
SECRET_KEY=your-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database Settings
DATABASE_URL=sqlite:///./twarga_cloud.db

# VM Settings
VM_BASE_DIR=./vms
VM_DEFAULT_RAM=1024
VM_DEFAULT_CPU=1
VM_DEFAULT_DISK=20

# Monitoring Settings
METRICS_COLLECTION_INTERVAL=5
METRICS_RETENTION_DAYS=7

# Terminal Settings
TTYD_BASE_PORT=7681
TERMINAL_SESSION_TIMEOUT=1800

# Resource Limits
MAX_VMS_PER_USER=5
MAX_TOTAL_RAM=8192
MAX_TOTAL_CPU=8

# Default User Credits
DEFAULT_USER_CREDITS=1000
```

### Database Configuration

The application uses SQLite by default. The database is automatically created during setup.

To reset the database:

```bash
# Backup existing database
cp twarga_cloud.db twarga_cloud.db.backup

# Delete database
rm twarga_cloud.db

# Reinitialize
python -c "from backend.database import init_db; init_db()"
```

### VM Storage Configuration

VMs are stored in the `vms/` directory by default. Each user's VMs are in separate subdirectories:

```
vms/
├── user1-vm1/
│   ├── Vagrantfile
│   └── .vm_info
├── user1-vm2/
└── user2-vm1/
```

To change the VM storage location, update `VM_BASE_DIR` in `.env`.

---

## Starting the Application

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Start the application with auto-reload
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at:
- **Main Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

### Production Mode

For production deployment, use a production ASGI server:

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn (4 worker processes)
gunicorn backend.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Running as a System Service

Create a systemd service file for automatic startup:

```bash
# Create service file
sudo nano /etc/systemd/system/twarga-cloud.service
```

Add the following content:

```ini
[Unit]
Description=Twarga Cloud Service
After=network.target

[Service]
Type=notify
User=yourusername
Group=yourusername
WorkingDirectory=/path/to/twarga-cloud
Environment="PATH=/path/to/twarga-cloud/venv/bin"
ExecStart=/path/to/twarga-cloud/venv/bin/gunicorn backend.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service on boot
sudo systemctl enable twarga-cloud

# Start service
sudo systemctl start twarga-cloud

# Check status
sudo systemctl status twarga-cloud
```

---

## Creating Admin Account

### Option 1: Using the Registration UI

1. Navigate to http://localhost:8000/register
2. Register with username `admin` (first user gets admin privileges)
3. Login at http://localhost:8000

### Option 2: Using Python Script

```bash
# Activate virtual environment
source venv/bin/activate

# Create admin user via Python
python3 << EOF
from backend.database import SessionLocal
from backend.models import User
from passlib.context import CryptContext

db = SessionLocal()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

admin = User(
    username="admin",
    email="admin@twarga.local",
    hashed_password=pwd_context.hash("admin123"),
    is_admin=True,
    is_active=True,
    credits=10000
)

db.add(admin)
db.commit()
print("Admin user created successfully!")
db.close()
EOF
```

### Option 3: Using SQL

```bash
sqlite3 twarga_cloud.db << EOF
INSERT INTO users (username, email, hashed_password, is_admin, is_active, credits, created_at)
VALUES (
    'admin',
    'admin@twarga.local',
    '\$2b\$12\$your-hashed-password-here',
    1,
    1,
    10000,
    datetime('now')
);
EOF
```

---

## Verification

### 1. Check Application Status

```bash
# Check if the application is running
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy","database":"connected"}
```

### 2. Access Web Interface

Open your browser and navigate to:
- **Main Page**: http://localhost:8000
- **Login**: http://localhost:8000/login
- **API Docs**: http://localhost:8000/docs

### 3. Test VM Creation

1. Login to the dashboard
2. Click "Launch New VM"
3. Fill in the form and create a VM
4. Wait for the VM to start
5. Access the terminal when ready

### 4. Check System Monitoring

Navigate to http://localhost:8000/monitor to see:
- Host system metrics
- VM resource usage
- Real-time charts

### 5. View SOC Feed

Navigate to http://localhost:8000/soc to see:
- System events
- VM lifecycle events
- Security alerts

---

## Post-Installation

### Security Hardening

#### 1. Change Default Credentials

```bash
# Generate a secure secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env file with the new secret key
```

#### 2. Configure Firewall

```bash
# Allow only necessary ports
sudo ufw allow 8000/tcp
sudo ufw enable
```

#### 3. Enable HTTPS (Production)

Use a reverse proxy like Nginx with Let's Encrypt:

```bash
# Install Nginx
sudo apt install nginx certbot python3-certbot-nginx

# Configure Nginx
sudo nano /etc/nginx/sites-available/twarga-cloud
```

Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/twarga-cloud /etc/nginx/sites-enabled/

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Test and reload Nginx
sudo nginx -t
sudo systemctl reload nginx
```

### Monitoring and Maintenance

#### 1. Log Rotation

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/twarga-cloud
```

```
/path/to/twarga-cloud/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 yourusername yourusername
    sharedscripts
}
```

#### 2. Database Backups

```bash
# Create backup script
nano backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DB_FILE="/path/to/twarga-cloud/twarga_cloud.db"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup
cp "$DB_FILE" "$BACKUP_DIR/twarga_cloud_$DATE.db"

# Keep only last 7 backups
ls -t "$BACKUP_DIR"/twarga_cloud_*.db | tail -n +8 | xargs rm -f
```

```bash
# Make executable
chmod +x backup.sh

# Add to crontab (daily backup at 2 AM)
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

#### 3. System Updates

```bash
# Update application dependencies
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Restart service
sudo systemctl restart twarga-cloud
```

---

## Troubleshooting

If you encounter issues during installation, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common problems and solutions.

Common installation issues:
- **KVM not available**: Ensure VT-x/AMD-V is enabled in BIOS
- **Permission denied errors**: Add user to `libvirt` and `kvm` groups
- **Port already in use**: Change the port in the startup command
- **Database errors**: Delete and reinitialize the database

---

## Next Steps

Now that Twarga Cloud is installed:

1. **Read the User Guide**: See [USER_GUIDE.md](USER_GUIDE.md) for feature documentation
2. **Explore the API**: Visit http://localhost:8000/docs
3. **Create VMs**: Launch your first virtual machine
4. **Monitor System**: Check the monitoring dashboard
5. **Review Security Events**: Explore the SOC feed

For development and customization, see [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md).

---

**Installation Complete! 🎉**

Need help? Check the [troubleshooting guide](TROUBLESHOOTING.md) or open an issue on GitHub.
