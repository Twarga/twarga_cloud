# 📖 User Guide - Twarga Cloud

Welcome to Twarga Cloud! This guide will help you get started with managing virtual machines, monitoring resources, and using all the features available to you.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [User Dashboard](#user-dashboard)
- [Managing Virtual Machines](#managing-virtual-machines)
- [Web Terminal Access](#web-terminal-access)
- [System Monitoring](#system-monitoring)
- [Security Events](#security-events)
- [User Settings](#user-settings)
- [Credits System](#credits-system)
- [Best Practices](#best-practices)

---

## Getting Started

### Creating an Account

1. Navigate to http://localhost:8000/register
2. Fill in the registration form:
   - **Username**: Your unique username (3-20 characters)
   - **Email**: Your email address
   - **Password**: Strong password (minimum 8 characters)
3. Click "Register"
4. You'll be automatically logged in

**Note**: The first user to register will be granted admin privileges automatically.

### Logging In

1. Navigate to http://localhost:8000/login
2. Enter your username and password
3. Click "Login"
4. You'll be redirected to your dashboard

### Understanding Your Credits

When you create an account, you start with **1,000 credits**. Credits are used to:
- Create virtual machines (cost varies by resources)
- Keep VMs running (ongoing cost)

**VM Costs:**
- **RAM**: 10 credits per GB per hour
- **CPU**: 5 credits per core per hour
- **Disk**: 1 credit per GB (one-time)

---

## User Dashboard

The dashboard is your main control center at http://localhost:8000/dashboard.

### Dashboard Overview

The dashboard displays:

#### 1. **Statistics Cards**
- **Available Credits**: Your current credit balance
- **Active VMs**: Number of running VMs
- **Total VMs**: Total VMs you've created

#### 2. **VM List**
Shows all your virtual machines with:
- VM name and status (running, stopped, pending, error)
- Resource allocation (RAM, CPU, disk)
- IP address (when running)
- Uptime
- Action buttons

#### 3. **Quick Actions**
- **Launch New VM**: Create a new virtual machine
- **Refresh**: Update VM status manually
- **Dark Mode Toggle**: Switch between light and dark themes

---

## Managing Virtual Machines

### Creating a New VM

1. Click the **"Launch New VM"** button
2. Fill in the VM creation form:

   **Basic Information:**
   - **VM Name**: Unique name for your VM (lowercase, numbers, hyphens only)
   - **Operating System**: Choose from available OS options
     - Ubuntu 20.04 LTS
     - Ubuntu 22.04 LTS
     - Debian 11
     - Debian 12
     - CentOS 7
     - CentOS 8

   **Resource Allocation:**
   - **RAM**: 512 MB to 4 GB
   - **CPU Cores**: 1 to 4 cores
   - **Disk Space**: 10 GB to 50 GB

3. Review the **estimated cost** displayed at the bottom
4. Click **"Create VM"**
5. Wait for the VM to be provisioned (this can take 2-5 minutes)

**Tips:**
- Start with minimal resources and scale up if needed
- Use descriptive names for easy identification
- Check your credit balance before creating VMs

### Understanding VM Status

| Status | Description | Available Actions |
|--------|-------------|-------------------|
| **Pending** | VM is being created | Wait |
| **Running** | VM is active and accessible | Stop, Restart, Terminal, Destroy |
| **Stopped** | VM is shut down but preserved | Start, Destroy |
| **Error** | VM encountered an error | View details, Destroy |

### Starting a VM

1. Locate the stopped VM in your VM list
2. Click the **"Start"** button
3. Wait for the status to change to "running"
4. The VM's IP address will be displayed

### Stopping a VM

1. Locate the running VM in your VM list
2. Click the **"Stop"** button
3. Confirm the action
4. The VM will shut down gracefully

**Note**: Stopping a VM preserves its state. You can restart it later without losing data.

### Restarting a VM

1. Locate the running VM in your VM list
2. Click the **"Restart"** button
3. The VM will reboot

**Use Cases:**
- Apply system updates
- Refresh network configuration
- Recover from hanging processes

### Destroying a VM

⚠️ **Warning**: This action is permanent and cannot be undone!

1. Locate the VM you want to delete
2. Click the **"Destroy"** button
3. Read the confirmation dialog carefully
4. Type the VM name to confirm
5. Click **"Yes, Destroy"**

**What happens:**
- The VM is permanently deleted
- All data on the VM is lost
- VM directory is removed
- Credits are NOT refunded

### Viewing VM Details

1. Click the **"Details"** button on any VM
2. View comprehensive information:
   - VM ID and name
   - Current status
   - Resource allocation
   - IP address
   - Uptime
   - Creation date
   - Operating system

---

## Web Terminal Access

Access your VMs directly from your browser!

### Opening a Terminal

1. Ensure your VM status is **"Running"**
2. Click the **"Terminal"** button
3. Wait for the terminal to connect (usually 2-3 seconds)
4. You're now connected via SSH!

### Using the Terminal

The web terminal provides full SSH access with:
- **Copy/Paste**: Use Ctrl+Shift+C and Ctrl+Shift+V
- **Command History**: Use Up/Down arrows
- **Tab Completion**: Press Tab for auto-completion
- **Multiple Sessions**: Open multiple terminals in separate browser tabs

**Default Credentials:**
- **Username**: `vagrant`
- **Password**: `vagrant` (or use SSH key authentication)

### Terminal Features

- **Clipboard Support**: Copy commands and paste output
- **Resizable**: Adjust terminal window size
- **Session Persistence**: Session remains active until you close it
- **Auto-reconnect**: Automatically reconnects if connection drops

### Closing a Terminal

1. Type `exit` or press Ctrl+D in the terminal
2. Or click the **"Close"** button in the terminal window

**Note**: Terminal sessions automatically expire after 30 minutes of inactivity.

### Terminal Troubleshooting

**Can't connect to terminal?**
- Ensure the VM is running
- Check if ttyd is installed on the host
- Verify the VM has an IP address
- Try restarting the VM

**Terminal is slow?**
- Check system resources on the monitoring page
- Reduce number of active terminal sessions
- Consider increasing VM RAM allocation

---

## System Monitoring

Monitor your system resources at http://localhost:8000/monitor.

### Host Metrics

View real-time metrics for the host system:

#### System Overview
- **CPU Usage**: Current CPU utilization percentage
- **Memory Usage**: RAM usage percentage and absolute values
- **Disk Usage**: Storage space used and available
- **Network I/O**: Current network traffic (incoming/outgoing)

#### Live Charts
- **CPU Usage Chart**: 60-second history graph
- **Memory Usage Chart**: Real-time RAM consumption
- **Disk Usage Chart**: Storage utilization over time
- **Network I/O Chart**: Network traffic visualization

### VM-Specific Metrics

For each running VM, view:
- **CPU Usage**: Per-VM processor utilization
- **Memory Usage**: RAM consumption by the VM
- **Disk Usage**: Storage used by the VM
- **Network Stats**: Data received/transmitted
- **Uptime**: How long the VM has been running
- **IP Address**: Current network address

### Resource Alerts

The monitoring page displays alerts when:
- CPU usage exceeds 90% (Critical)
- Memory usage exceeds 85% (Warning)
- Disk usage exceeds 90% (Critical)
- Swap usage exceeds 50% (Warning)

**Alert Colors:**
- 🔴 **Red**: Critical (≥90%)
- 🟡 **Yellow**: Warning (≥75%)
- 🟢 **Green**: Normal (<75%)

### Monitoring Features

- **Auto-refresh**: Metrics update every 5 seconds automatically
- **Historical Data**: View up to 7 days of metric history
- **Export Data**: Download metrics as JSON for analysis
- **Multi-VM View**: See all VM metrics in one place

### Using Monitoring Data

**Identify Resource Bottlenecks:**
- High CPU usage → Add more cores or stop other VMs
- High memory usage → Increase RAM or reduce VM count
- High disk usage → Clean up files or expand storage

**Optimize VM Performance:**
- Monitor VM metrics to identify slow VMs
- Adjust resource allocation based on actual usage
- Schedule resource-intensive tasks during low-usage periods

---

## Security Events

View security and operational events at http://localhost:8000/soc.

### SOC Dashboard Overview

The Security Operations Center (SOC) dashboard displays:

#### Event Statistics
- **Total Events**: Count of all logged events
- **Info Events**: Informational messages (blue)
- **Warning Events**: Warning-level events (yellow)
- **Critical Events**: Critical security events (red)

#### Event Feed
Real-time feed of all system events, including:
- VM lifecycle events (created, started, stopped, destroyed)
- Authentication events (login, logout, failed attempts)
- System events (resource alerts, errors)
- Security events (brute force attempts, suspicious activity)

### Event Types

| Type | Description | Examples |
|------|-------------|----------|
| **VM** | VM lifecycle events | VM created, started, stopped |
| **Auth** | Authentication events | Login, logout, failed attempts |
| **System** | System-level events | Resource alerts, errors |
| **Security** | Security incidents | Brute force, suspicious activity |

### Event Severity Levels

- **Info**: Normal operations (blue badge)
- **Warning**: Potential issues (yellow badge)
- **Critical**: Security threats or critical errors (red badge)

### Filtering Events

Use the filter panel to narrow down events:

1. **By Type**: Select VM, Auth, System, or Security
2. **By Severity**: Filter by Info, Warning, or Critical
3. **By Time Range**: 
   - Last hour
   - Last 24 hours
   - Last 7 days
   - Last 30 days
4. **By Search**: Search event messages, types, or severities

### Viewing Event Details

1. Click on any event card in the feed
2. View detailed information:
   - Event ID
   - Timestamp
   - Event type and severity
   - Full message
   - Associated VM ID (if applicable)
   - User ID
   - Additional JSON details

### Exporting Events

1. Apply desired filters to the event feed
2. Click the **"Export Events"** button
3. Events are downloaded as a JSON file
4. Use for analysis or record-keeping

### Security Best Practices

**Monitor for:**
- Multiple failed login attempts
- Unusual VM creation patterns
- Resource usage spikes
- SSH brute force attempts

**Respond to alerts by:**
- Investigating critical events immediately
- Reviewing warning events daily
- Analyzing patterns over time
- Reporting suspicious activity to admins

---

## User Settings

### Account Information

View and manage your account:
- Username (cannot be changed)
- Email address
- Account creation date
- Current role (User or Admin)

### Changing Password

1. Click your username in the top-right corner
2. Select "Account Settings"
3. Enter your current password
4. Enter new password twice
5. Click "Update Password"

**Password Requirements:**
- Minimum 8 characters
- Mix of letters and numbers recommended
- Special characters encouraged

### Theme Preferences

Toggle between light and dark mode:
1. Click the moon/sun icon in the header
2. Your preference is saved automatically
3. Theme applies across all pages

---

## Credits System

### Understanding Credits

Credits are the virtual currency used to pay for VM resources.

**Starting Credits**: 1,000 credits
**Credit Costs**:
- RAM: 10 credits/GB/hour
- CPU: 5 credits/core/hour
- Disk: 1 credit/GB (one-time)

### Checking Your Balance

Your current credit balance is displayed:
- In the dashboard statistics card
- In the header (next to your username)
- Before creating a new VM

### Credit Consumption

**One-time Costs:**
- VM creation (disk allocation)

**Ongoing Costs:**
- Running VMs consume credits per hour
- Stopped VMs do NOT consume credits

### Low Credit Warnings

You'll receive warnings when:
- Credits fall below 100
- You attempt to create a VM you can't afford
- A running VM would consume your last credits

### Getting More Credits

**Option 1: Contact Admin**
- Request a credit adjustment from an administrator
- Provide a reason for the request

**Option 2: Stop Unused VMs**
- Stop VMs when not in use
- Destroy VMs you no longer need

**Option 3: Optimize Resources**
- Use smaller VM sizes
- Monitor actual resource usage
- Right-size your VMs

---

## Best Practices

### VM Management

✅ **Do:**
- Use descriptive VM names
- Stop VMs when not in use
- Monitor resource usage regularly
- Destroy unused VMs
- Keep VMs updated and patched

❌ **Don't:**
- Leave VMs running unnecessarily
- Create more VMs than you need
- Use maximum resources "just in case"
- Ignore resource alerts
- Forget to backup important data

### Security

✅ **Do:**
- Use strong, unique passwords
- Change default VM passwords
- Monitor the SOC feed regularly
- Report suspicious activity
- Log out when finished

❌ **Don't:**
- Share your account credentials
- Use weak passwords
- Ignore security alerts
- Leave terminal sessions open
- Access from untrusted networks

### Resource Optimization

✅ **Do:**
- Start with minimal resources
- Scale up based on actual usage
- Monitor performance metrics
- Stop VMs during off-hours
- Review credit consumption weekly

❌ **Don't:**
- Over-provision resources
- Run multiple idle VMs
- Ignore performance issues
- Max out all resources
- Waste credits on unused capacity

### Troubleshooting

✅ **Do:**
- Check the SOC feed for errors
- Review VM details when issues occur
- Try restarting problematic VMs
- Contact admin if stuck
- Read the troubleshooting guide

❌ **Don't:**
- Repeatedly destroy and recreate VMs
- Ignore error messages
- Make random changes
- Skip documentation
- Panic!

---

## Keyboard Shortcuts

Speed up your workflow with keyboard shortcuts:

| Shortcut | Action |
|----------|--------|
| `Alt + N` | Launch new VM modal |
| `Alt + M` | Go to monitoring page |
| `Alt + S` | Go to SOC page |
| `Alt + D` | Go to dashboard |
| `Alt + T` | Toggle dark mode |
| `Esc` | Close any open modal |

---

## Getting Help

### Documentation

- **User Guide**: This document
- **Installation Guide**: [INSTALL.md](INSTALL.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Developer Guide**: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)

### Support Channels

1. **Check Documentation**: Most questions are answered in the guides
2. **Review Troubleshooting**: Common issues and solutions
3. **Contact Admin**: For account or credit issues
4. **GitHub Issues**: Report bugs or request features
5. **Community Discussions**: Ask questions and share tips

### Common Questions

**Q: How do I get more credits?**
A: Contact your administrator to request a credit adjustment.

**Q: Can I increase VM resources after creation?**
A: Currently, no. You'll need to create a new VM with different specs.

**Q: How long does VM creation take?**
A: Typically 2-5 minutes depending on the OS and host performance.

**Q: Can I access VMs from outside the browser?**
A: Yes, use SSH with the VM's IP address and port 22.

**Q: What happens if I run out of credits?**
A: Your running VMs will continue, but you can't create new ones.

**Q: Can I transfer credits to another user?**
A: No, only administrators can adjust user credits.

**Q: How do I backup my VM data?**
A: Use the terminal to copy data to an external location, or contact your admin for backup options.

---

## Tips and Tricks

### Efficient VM Management

1. **Use templates**: Create a base VM and clone it (future feature)
2. **Tag your VMs**: Use naming conventions like `project-env-purpose`
3. **Schedule start/stop**: Note down when you actually need VMs
4. **Monitor costs**: Check credit consumption weekly

### Terminal Productivity

1. **Use screen/tmux**: Keep sessions alive across disconnects
2. **Save scripts**: Store common commands in files
3. **Use aliases**: Create shortcuts for frequent commands
4. **Keep logs**: Redirect output to files for later review

### Monitoring Insights

1. **Baseline metrics**: Note normal resource usage levels
2. **Set reminders**: Check monitoring daily
3. **Watch trends**: Look for gradual increases in resource use
4. **Compare VMs**: Identify which VMs use most resources

---

**Need more help?** Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or contact your administrator.

Happy cloud computing! ☁️
