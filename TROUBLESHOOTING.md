# 🔧 Troubleshooting Guide - Twarga Cloud

This guide helps you diagnose and fix common issues with Twarga Cloud.

## 📋 Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Installation Issues](#installation-issues)
- [Authentication Problems](#authentication-problems)
- [VM Management Issues](#vm-management-issues)
- [Terminal Access Problems](#terminal-access-problems)
- [Monitoring Issues](#monitoring-issues)
- [Database Problems](#database-problems)
- [Performance Issues](#performance-issues)
- [Network Issues](#network-issues)
- [Getting More Help](#getting-more-help)

---

## Quick Diagnostics

### Health Check

Run this quick health check to identify common issues:

```bash
# 1. Check if application is running
curl http://localhost:8000/health

# Expected: {"status":"healthy","database":"connected"}

# 2. Check Python version
python3 --version
# Expected: Python 3.11.0 or higher

# 3. Check if virtual environment is activated
which python
# Expected: /path/to/twarga-cloud/venv/bin/python

# 4. Check Vagrant installation
vagrant --version
# Expected: Vagrant 2.2.0 or higher

# 5. Check KVM/libvirt status
sudo systemctl status libvirtd
# Expected: active (running)

# 6. Check if port 8000 is available
netstat -tuln | grep 8000
# If output exists, port is in use

# 7. Check database file
ls -lh twarga_cloud.db
# Should exist with size > 0

# 8. Check VM directory
ls -la vms/
# Should exist and be writable

# 9. Check log files
ls -la logs/
# Should contain events.log
```

### System Requirements Check

```bash
# Check CPU cores
nproc
# Minimum: 4 cores

# Check RAM
free -h
# Minimum: 8 GB

# Check disk space
df -h .
# Minimum: 50 GB free

# Check if KVM is supported
egrep -c '(vmx|svm)' /proc/cpuinfo
# Should be > 0
```

---

## Installation Issues

### Issue: Python version too old

**Symptoms:**
```
ERROR: This package requires Python 3.11 or higher
```

**Solution:**
```bash
# Install Python 3.11+ on Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# Set Python 3.11 as default (optional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Recreate virtual environment
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: pip install fails with "No module named '_sqlite3'"

**Symptoms:**
```
ModuleNotFoundError: No module named '_sqlite3'
```

**Solution:**
```bash
# Install SQLite development libraries
sudo apt install libsqlite3-dev

# Rebuild Python (if installed from source)
cd /path/to/python/source
./configure --enable-loadable-sqlite-extensions
make
sudo make install
```

### Issue: vagrant-libvirt plugin fails to install

**Symptoms:**
```
ERROR: Failed building gem native extension
```

**Solution:**
```bash
# Install build dependencies
sudo apt install build-essential libvirt-dev ruby-dev

# Clear existing plugin
vagrant plugin uninstall vagrant-libvirt

# Reinstall
vagrant plugin install vagrant-libvirt

# Verify
vagrant plugin list
```

### Issue: KVM/libvirt not working

**Symptoms:**
```
ERROR: KVM kernel module is not loaded
```

**Solution:**
```bash
# Check if KVM modules are loaded
lsmod | grep kvm
# Should see kvm_intel or kvm_amd

# Load KVM module manually
sudo modprobe kvm
sudo modprobe kvm_intel  # or kvm_amd for AMD CPUs

# Enable on boot
echo "kvm" | sudo tee -a /etc/modules
echo "kvm_intel" | sudo tee -a /etc/modules  # or kvm_amd

# Add user to required groups
sudo usermod -aG libvirt $USER
sudo usermod -aG kvm $USER

# Log out and back in for group changes to take effect
# Or use: newgrp libvirt
```

### Issue: Permission denied errors

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: 'vms/'
```

**Solution:**
```bash
# Fix directory permissions
sudo chown -R $USER:$USER /path/to/twarga-cloud
chmod -R 755 /path/to/twarga-cloud

# Fix libvirt permissions
sudo usermod -aG libvirt $USER
sudo usermod -aG kvm $USER
newgrp libvirt

# Restart libvirt
sudo systemctl restart libvirtd
```

---

## Authentication Problems

### Issue: Cannot login - "Invalid credentials"

**Symptoms:**
- Login fails with valid credentials
- "Invalid username or password" error

**Solution:**

1. **Verify user exists:**
```bash
sqlite3 twarga_cloud.db "SELECT username, is_active FROM users;"
```

2. **Check if user is active:**
```bash
sqlite3 twarga_cloud.db "UPDATE users SET is_active = 1 WHERE username = 'youruser';"
```

3. **Reset password:**
```bash
python3 << EOF
from backend.database import SessionLocal
from backend.models import User
from backend.auth import get_password_hash

db = SessionLocal()
user = db.query(User).filter(User.username == "youruser").first()
if user:
    user.hashed_password = get_password_hash("newpassword")
    db.commit()
    print("Password reset successfully")
else:
    print("User not found")
db.close()
EOF
```

### Issue: JWT token expired

**Symptoms:**
```
{"detail": "Could not validate credentials"}
```

**Solution:**
1. **Clear browser storage:**
```javascript
// In browser console
localStorage.clear();
location.reload();
```

2. **Login again** to get a new token

3. **Increase token expiration time** (in .env):
```ini
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
```

### Issue: Cannot access admin features

**Symptoms:**
- 403 Forbidden on admin routes
- "Not authorized" message

**Solution:**

1. **Check if user is admin:**
```bash
sqlite3 twarga_cloud.db "SELECT username, is_admin FROM users WHERE username = 'youruser';"
```

2. **Grant admin privileges:**
```bash
sqlite3 twarga_cloud.db "UPDATE users SET is_admin = 1 WHERE username = 'youruser';"
```

3. **Login again** to refresh token with new permissions

---

## VM Management Issues

### Issue: VM creation fails

**Symptoms:**
```
Error: Failed to create VM
VM status: error
```

**Diagnosis:**
```bash
# Check Vagrant status
cd vms/user{id}-{vmname}/
vagrant status

# Check Vagrant logs
vagrant up --debug

# Check libvirt connection
virsh list --all

# Check system resources
free -h
df -h
```

**Solutions:**

1. **Insufficient credits:**
```bash
# Add credits via admin panel or database
sqlite3 twarga_cloud.db "UPDATE users SET credits = credits + 1000 WHERE id = 1;"
```

2. **Not enough resources:**
```bash
# Check available RAM
free -h

# Stop other VMs
# Via dashboard or:
vagrant halt
```

3. **Vagrant box not found:**
```bash
# Add box manually
vagrant box add ubuntu/focal64

# List available boxes
vagrant box list
```

4. **VM name conflict:**
```bash
# Choose a different name or destroy existing VM
vagrant destroy -f
```

### Issue: VM won't start

**Symptoms:**
- VM status stuck on "pending"
- Start button doesn't work
- Error: "Failed to start VM"

**Diagnosis:**
```bash
cd vms/user{id}-{vmname}/
vagrant status
vagrant up --debug
```

**Solutions:**

1. **VM is already running:**
```bash
# Check actual status
virsh list --all

# Force reload
vagrant reload
```

2. **Libvirt network issue:**
```bash
# Restart libvirt
sudo systemctl restart libvirtd

# Check network
virsh net-list --all
virsh net-start default
```

3. **Corrupted VM state:**
```bash
# Destroy and recreate
vagrant destroy -f
# Then create new VM via dashboard
```

### Issue: VM won't stop

**Symptoms:**
- Stop command times out
- VM remains in "running" state

**Solution:**
```bash
cd vms/user{id}-{vmname}/

# Try graceful halt
vagrant halt

# Force halt if needed
vagrant halt --force

# As last resort, use virsh
virsh list --all
virsh destroy {domain-name}
```

### Issue: Cannot destroy VM

**Symptoms:**
```
Error: Failed to destroy VM
```

**Solution:**
```bash
cd vms/user{id}-{vmname}/

# Force destroy
vagrant destroy -f

# Clean up VM directory
cd ..
rm -rf user{id}-{vmname}/

# Update database
sqlite3 twarga_cloud.db "DELETE FROM vms WHERE name = 'vmname';"
```

### Issue: VM has no IP address

**Symptoms:**
- IP address shows as "N/A"
- Cannot connect to terminal

**Diagnosis:**
```bash
cd vms/user{id}-{vmname}/
vagrant ssh-config
```

**Solutions:**

1. **Wait for DHCP:**
```bash
# Wait 30-60 seconds for IP assignment
# Restart networking in VM
vagrant ssh -c "sudo systemctl restart networking"
```

2. **Restart VM:**
```bash
vagrant reload
```

3. **Check libvirt network:**
```bash
virsh net-list --all
virsh net-start default
```

---

## Terminal Access Problems

### Issue: Terminal won't open

**Symptoms:**
- Terminal button doesn't respond
- "Failed to connect" error
- Blank terminal screen

**Diagnosis:**
```bash
# Check if ttyd is installed
which ttyd

# Check if terminal session exists
ps aux | grep ttyd

# Check logs
tail -f logs/events.log | grep terminal
```

**Solutions:**

1. **ttyd not installed:**
```bash
# Install ttyd
sudo apt install ttyd

# Or build from source
git clone https://github.com/tsl0922/ttyd.git
cd ttyd && mkdir build && cd build
cmake ..
make && sudo make install
```

2. **VM not running:**
```bash
# Verify VM status
vagrant status

# Start VM if stopped
vagrant up
```

3. **Port already in use:**
```bash
# Check used ports
netstat -tuln | grep 768

# Kill conflicting process
sudo kill $(lsof -t -i:7681)
```

4. **Session timeout:**
```bash
# Close and reopen terminal
# Sessions expire after 30 minutes
```

### Issue: Terminal is very slow

**Symptoms:**
- Characters appear with delay
- Commands take long to execute

**Solutions:**

1. **Check system resources:**
```bash
# Monitor CPU and memory
top
htop
```

2. **Reduce VM load:**
```bash
# Stop unnecessary processes in VM
vagrant ssh
top
# Kill resource-heavy processes
```

3. **Increase VM resources:**
```bash
# Destroy and recreate with more RAM/CPU
vagrant destroy -f
# Create new VM with higher specs
```

### Issue: Copy/paste doesn't work in terminal

**Symptoms:**
- Cannot paste commands
- Clipboard operations fail

**Solutions:**

1. **Use correct shortcuts:**
- Copy: `Ctrl+Shift+C` (not Ctrl+C)
- Paste: `Ctrl+Shift+V` (not Ctrl+V)

2. **Check browser permissions:**
- Allow clipboard access in browser settings
- Try different browser (Chrome/Firefox)

3. **Use terminal commands:**
```bash
# Upload file content
cat > file.txt << EOF
paste content here
EOF
```

---

## Monitoring Issues

### Issue: Metrics not updating

**Symptoms:**
- Charts show flat lines
- Metrics stuck at old values
- "No data available" message

**Solutions:**

1. **Check monitoring service:**
```bash
# Verify metrics collection
curl http://localhost:8000/api/metrics/host

# Check database
sqlite3 twarga_cloud.db "SELECT COUNT(*) FROM metrics;"
```

2. **Restart application:**
```bash
# Stop FastAPI
# (Ctrl+C if running in terminal)

# Restart
uvicorn backend.main:app --reload
```

3. **Clear old metrics:**
```bash
# Via API (admin only)
curl -X DELETE http://localhost:8000/api/metrics/cleanup \
  -H "Authorization: Bearer {admin_token}"

# Or via database
sqlite3 twarga_cloud.db "DELETE FROM metrics WHERE timestamp < datetime('now', '-7 days');"
```

### Issue: High CPU usage from monitoring

**Symptoms:**
- System slow after starting monitoring
- CPU constantly at 100%

**Solutions:**

1. **Increase collection interval:**
```python
# In backend/monitor.py
# Change interval from 5 seconds to 10 or 15
COLLECTION_INTERVAL = 15  # seconds
```

2. **Disable auto-refresh:**
```javascript
// In monitor.html
// Increase refresh interval or disable
```

3. **Reduce metric retention:**
```bash
# Keep only recent metrics
sqlite3 twarga_cloud.db "DELETE FROM metrics WHERE timestamp < datetime('now', '-24 hours');"
```

---

## Database Problems

### Issue: Database locked

**Symptoms:**
```
sqlite3.OperationalError: database is locked
```

**Solutions:**

1. **Close other connections:**
```bash
# Find processes using database
lsof twarga_cloud.db

# Kill them if necessary
kill -9 {PID}
```

2. **Enable WAL mode:**
```bash
sqlite3 twarga_cloud.db "PRAGMA journal_mode=WAL;"
```

3. **Increase timeout:**
```python
# In backend/database.py
engine = create_engine(
    DATABASE_URL,
    connect_args={"timeout": 30}  # Increase timeout
)
```

### Issue: Database corruption

**Symptoms:**
```
sqlite3.DatabaseError: database disk image is malformed
```

**Solutions:**

1. **Try to recover:**
```bash
# Dump database
sqlite3 twarga_cloud.db .dump > backup.sql

# Recreate database
rm twarga_cloud.db
sqlite3 twarga_cloud.db < backup.sql
```

2. **Restore from backup:**
```bash
# If you have a backup
cp twarga_cloud.db.backup twarga_cloud.db
```

3. **Reinitialize (last resort):**
```bash
# ⚠️ This will delete all data!
rm twarga_cloud.db
python -c "from backend.database import init_db; init_db()"
```

### Issue: Cannot connect to database

**Symptoms:**
```
{"status":"unhealthy","database":"disconnected"}
```

**Solutions:**

1. **Check database file:**
```bash
ls -lh twarga_cloud.db
# Should exist and be readable

# Fix permissions if needed
chmod 644 twarga_cloud.db
```

2. **Check database URL:**
```bash
# In .env
DATABASE_URL=sqlite:///./twarga_cloud.db

# Make sure path is correct
```

3. **Reinitialize database:**
```bash
python -c "from backend.database import init_db; init_db()"
```

---

## Performance Issues

### Issue: Slow response times

**Symptoms:**
- Pages take long to load
- API requests timeout
- UI feels sluggish

**Diagnosis:**
```bash
# Check system resources
top
htop
iotop  # Disk I/O

# Check database size
ls -lh twarga_cloud.db

# Check VM count
virsh list --all | wc -l
```

**Solutions:**

1. **Optimize database:**
```bash
sqlite3 twarga_cloud.db "VACUUM;"
sqlite3 twarga_cloud.db "ANALYZE;"
```

2. **Clean up old data:**
```bash
# Remove old metrics
sqlite3 twarga_cloud.db "DELETE FROM metrics WHERE timestamp < datetime('now', '-7 days');"

# Remove old events
sqlite3 twarga_cloud.db "DELETE FROM events WHERE timestamp < datetime('now', '-30 days');"
```

3. **Stop unused VMs:**
```bash
# Via dashboard or:
cd vms/user{id}-{vmname}/
vagrant halt
```

4. **Increase worker processes:**
```bash
# Use gunicorn with multiple workers
gunicorn backend.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Issue: High memory usage

**Symptoms:**
- System runs out of RAM
- OOM killer terminates processes

**Solutions:**

1. **Check memory allocation:**
```bash
free -h
# See what's using memory
ps aux --sort=-%mem | head
```

2. **Reduce VM resources:**
```bash
# Use smaller VM sizes
# Stop VMs when not needed
```

3. **Add swap space:**
```bash
# Create 4GB swap file
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Issue: Disk space full

**Symptoms:**
```
OSError: [Errno 28] No space left on device
```

**Solutions:**

1. **Check disk usage:**
```bash
df -h
du -sh vms/*
du -sh logs/*
```

2. **Clean up VM directories:**
```bash
# Remove destroyed VMs
cd vms/
rm -rf user*/.vagrant/machines/*/libvirt/*.img

# Or use Vagrant cleanup
vagrant global-status --prune
```

3. **Compress logs:**
```bash
gzip logs/*.log
```

4. **Remove old Vagrant boxes:**
```bash
vagrant box list
vagrant box remove {box_name} --all
```

---

## Network Issues

### Issue: Cannot access application

**Symptoms:**
- Browser shows "Connection refused"
- Timeout when accessing localhost:8000

**Solutions:**

1. **Check if application is running:**
```bash
ps aux | grep uvicorn
# Or
curl http://localhost:8000/health
```

2. **Check port binding:**
```bash
netstat -tuln | grep 8000
# Should show: 0.0.0.0:8000 or 127.0.0.1:8000
```

3. **Check firewall:**
```bash
sudo ufw status
# Allow port if needed
sudo ufw allow 8000/tcp
```

4. **Try different port:**
```bash
uvicorn backend.main:app --port 8080
```

### Issue: VMs cannot reach internet

**Symptoms:**
- Cannot apt update in VM
- No internet connectivity

**Solutions:**

1. **Check libvirt network:**
```bash
virsh net-list --all
virsh net-start default

# Enable autostart
virsh net-autostart default
```

2. **Check host NAT:**
```bash
# Ensure forwarding is enabled
cat /proc/sys/net/ipv4/ip_forward
# Should be 1

# Enable if needed
sudo sysctl -w net.ipv4.ip_forward=1
```

3. **Restart networking:**
```bash
sudo systemctl restart libvirtd
vagrant reload
```

### Issue: Port conflict

**Symptoms:**
```
ERROR: Address already in use
```

**Solutions:**

1. **Find process using port:**
```bash
sudo lsof -i :8000
# Or
sudo netstat -tuln | grep 8000
```

2. **Kill conflicting process:**
```bash
sudo kill $(lsof -t -i:8000)
```

3. **Use different port:**
```bash
uvicorn backend.main:app --port 8001
```

---

## Getting More Help

### Logs to Check

1. **Application logs:**
```bash
# If running in terminal, check output
# Or check systemd logs:
sudo journalctl -u twarga-cloud -f
```

2. **Event logs:**
```bash
tail -f logs/events.log
tail -f logs/ssh_attempts.log
```

3. **Vagrant logs:**
```bash
cd vms/user{id}-{vmname}/
vagrant up --debug > vagrant.log 2>&1
cat vagrant.log
```

4. **Libvirt logs:**
```bash
sudo tail -f /var/log/libvirt/libvirtd.log
sudo tail -f /var/log/libvirt/qemu/*.log
```

### Diagnostic Information to Collect

When asking for help, provide:

```bash
# System information
uname -a
lsb_release -a

# Software versions
python3 --version
vagrant --version
virsh --version

# Application status
curl http://localhost:8000/health

# Database status
sqlite3 twarga_cloud.db "SELECT COUNT(*) FROM users;"
sqlite3 twarga_cloud.db "SELECT COUNT(*) FROM vms;"

# Resource usage
free -h
df -h
top -bn1 | head -20

# Recent errors
tail -50 logs/events.log
```

### Support Channels

1. **Documentation:**
   - README.md
   - USER_GUIDE.md
   - DEVELOPER_GUIDE.md
   - This file (TROUBLESHOOTING.md)

2. **GitHub Issues:**
   - Search existing issues
   - Create new issue with diagnostic info

3. **Community:**
   - GitHub Discussions
   - Stack Overflow (tag: twarga-cloud)

4. **Email:**
   - support@twarga.tech (if available)

### Before Asking for Help

- [ ] Check this troubleshooting guide
- [ ] Review documentation
- [ ] Search GitHub issues
- [ ] Try basic diagnostics
- [ ] Collect diagnostic information
- [ ] Note exact error messages
- [ ] List steps to reproduce

---

## Emergency Procedures

### Complete System Reset

⚠️ **Warning: This will delete all data!**

```bash
# Stop application
# (Ctrl+C if running in terminal)

# Stop all VMs
cd vms/
for dir in */; do
  cd "$dir"
  vagrant destroy -f
  cd ..
done

# Remove all VMs
rm -rf vms/*

# Reset database
rm twarga_cloud.db
python -c "from backend.database import init_db; init_db()"

# Clear logs
rm -f logs/*.log
touch logs/events.log
touch logs/ssh_attempts.log

# Restart application
source venv/bin/activate
uvicorn backend.main:app --reload
```

### Recovery Mode

If application won't start:

```bash
# 1. Check Python environment
source venv/bin/activate
which python
# Should be in venv

# 2. Reinstall dependencies
pip install --upgrade -r requirements.txt

# 3. Check database
sqlite3 twarga_cloud.db "PRAGMA integrity_check;"

# 4. Try minimal start
python3 << EOF
from backend.main import app
print("App loaded successfully")
EOF

# 5. Start in debug mode
python3 -m debugpy --listen 5678 --wait-for-client \
  -m uvicorn backend.main:app --reload
```

---

## Known Issues

### Issue: VMs slow on battery power (laptops)

**Cause:** CPU frequency scaling reduces performance

**Workaround:**
```bash
# Set performance governor
sudo cpupower frequency-set -g performance

# Or disable CPU scaling in BIOS
```

### Issue: Dark mode flickers

**Cause:** Theme loads after page render

**Workaround:** Refresh page or clear browser cache

### Issue: Vagrant libvirt plugin conflicts

**Cause:** Multiple Ruby versions or gem conflicts

**Solution:**
```bash
vagrant plugin uninstall vagrant-libvirt
gem cleanup
vagrant plugin install vagrant-libvirt
```

---

**Still stuck?** Open an issue on GitHub with:
- Detailed problem description
- Steps to reproduce
- Error messages
- Diagnostic information (see above)
- What you've already tried

We're here to help! 🚀
