# Web Terminal Setup Guide

## Overview
Twarga Cloud MVP now includes web-based terminal access to VMs via ttyd integration. This allows users to access their running VMs directly from the web interface.

## Prerequisites

### 1. Install ttyd
ttyd is required to provide web terminal functionality. Install it on your system:

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ttyd
```

**Fedora/RHEL:**
```bash
sudo dnf install ttyd
```

**Arch Linux:**
```bash
sudo pacman -S ttyd
```

**From Source:**
```bash
git clone https://github.com/tsl0922/ttyd.git
cd ttyd && mkdir build && cd build
cmake ..
make && sudo make install
```

### 2. Verify Installation
```bash
which ttyd
ttyd --version
```

## API Endpoints

### User Endpoints

#### Start Terminal Session
```http
POST /api/terminal/start/{vm_id}
Authorization: Bearer <token>
```

Response:
```json
{
  "session_id": "abc123...",
  "vm_id": 1,
  "vm_name": "my-ubuntu-vm",
  "port": 7681,
  "url": "http://localhost:7681",
  "token": "secure-token-here",
  "created_at": "2025-10-25T23:30:00",
  "message": "Terminal session started successfully"
}
```

#### Stop Terminal Session
```http
DELETE /api/terminal/stop/{vm_id}
Authorization: Bearer <token>
```

#### Get Terminal Session Info
```http
GET /api/terminal/session/{vm_id}
Authorization: Bearer <token>
```

#### List Active Sessions
```http
GET /api/terminal/sessions
Authorization: Bearer <token>
```

### Admin Endpoints

#### List All Sessions
```http
GET /api/admin/terminal/sessions
Authorization: Bearer <admin-token>
```

#### Cleanup Expired Sessions
```http
POST /api/admin/terminal/cleanup
Authorization: Bearer <admin-token>
```

#### Emergency Stop All Sessions
```http
POST /api/admin/terminal/stop-all
Authorization: Bearer <admin-token>
```

## Security Features

1. **Authentication**: Each terminal session requires authentication via ttyd's credential system
2. **Authorization**: Users can only access terminals for their own VMs (admins can access all)
3. **Session Tokens**: Unique secure tokens generated for each session
4. **Auto-Expiration**: Sessions automatically expire after 30 minutes of inactivity
5. **VM Status Check**: Terminal access only available for running VMs
6. **Event Logging**: All terminal access attempts logged to SOC feed

## How It Works

1. User requests terminal access for a running VM
2. System verifies user owns the VM and VM is running
3. TerminalManager spawns a ttyd process that connects to VM via `vagrant ssh`
4. ttyd listens on an allocated port (starting from 7681)
5. User accesses terminal via web browser at the provided URL
6. ttyd authenticates user with the provided token
7. Session is tracked and automatically cleaned up after timeout or manual stop

## Port Allocation

- Base port: 7681
- Each terminal session gets a unique port
- Ports are allocated sequentially (7681, 7682, 7683, etc.)
- Maximum 1000 concurrent sessions (ports 7681-8681)

## Session Management

- **Timeout**: 30 minutes of inactivity
- **Automatic Cleanup**: Expired sessions cleaned up periodically
- **Reuse**: If a session already exists for a VM, it's reused instead of creating a new one
- **Shutdown**: All sessions automatically stopped when application shuts down

## Troubleshooting

### ttyd not found
```
Error: Failed to start terminal session. Check if ttyd is installed...
```
**Solution**: Install ttyd using the instructions above

### VM not running
```
Error: VM is not running (current status: stopped)
```
**Solution**: Start the VM before accessing terminal

### Connection refused
**Solution**: Check that the ttyd process is running and the port is not blocked by firewall

### Session expired
**Solution**: Start a new terminal session - old sessions expire after 30 minutes

## Example Usage with curl

```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user&password=pass" | jq -r .access_token)

# Start terminal session for VM ID 1
curl -X POST http://localhost:8000/api/terminal/start/1 \
  -H "Authorization: Bearer $TOKEN"

# Output will include URL like http://localhost:7681
# Open this URL in browser and authenticate with username:token

# Stop session when done
curl -X DELETE http://localhost:8000/api/terminal/stop/1 \
  -H "Authorization: Bearer $TOKEN"
```

## Integration with Frontend

The terminal UI will be integrated in Phase 6.2 with:
- Terminal button on VM dashboard for running VMs
- Iframe embedding of ttyd terminal
- Automatic session management
- Connection status indicators
- Easy start/stop controls

## Technical Details

- **Technology**: ttyd (https://github.com/tsl0922/ttyd)
- **Protocol**: WebSocket over HTTP
- **Command**: `vagrant ssh` (automatic SSH to VM)
- **Authentication**: HTTP Basic Auth with token
- **Process Management**: subprocess.Popen with cleanup
- **Session Tracking**: In-memory dictionary with metadata
- **Event Logging**: All actions logged to Event model

## Notes

- Terminal sessions are bound to the application lifecycle
- Restarting the application will terminate all active sessions
- Each VM can have at most one active terminal session at a time
- Admin users can view and manage all terminal sessions
- Regular users can only access terminals for VMs they own
