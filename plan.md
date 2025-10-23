



☁️ Project: Twarga Cloud MVP – Local Cloud Simulation Lab

Goal: Build a local IaaS simulator that behaves like a small-scale version of Linode or DigitalOcean — deploy virtual machines, monitor them, and manage users — entirely on your laptop using FastAPI + Vagrant (KVM).

This isn’t just a web app — it’s a full cloud operations lab for learning VM orchestration, monitoring, and SOC visibility in one self-contained system.

🧩 1. Project Description

Twarga Cloud is a self-hosted mini cloud platform designed for educational use.
It lets a user:

Sign up and launch VMs with a few clicks

Interact with those VMs via web terminals

View live system resource metrics (CPU, RAM, disk usage)

Act as their own SOC (Security Operations Center) by viewing logs and events

🎯 Educational Purpose

This lab simulates:

A mini Infrastructure-as-a-Service (IaaS) platform

A Cloud Operations & Monitoring environment

A Security observation lab where you can simulate incidents, logs, and alerts

Think of it as your personal hybrid between Linode Manager and SOC dashboard — entirely offline.

🧱 2. MVP Scope
Category	Description
Users	Sign up, log in, manage credits, launch VMs
VM Management	Start, stop, destroy, list VMs
Monitoring	View host system metrics, per-VM resource usage
SOC Dashboard (Mini)	Display login attempts, SSH logs, VM events
Admin Panel	Manage users, credits, and monitor all VMs
Terminal Access	Web terminal access to running VMs (ttyd)
Persistence	SQLite DB for all users and VM metadata

⚡ The MVP runs entirely on a single machine using KVM/QEMU (via Vagrant-libvirt plugin).

👥 3. Roles and Access
🧑‍💻 User Role

Register an account

See personal credits

Launch up to N VMs with chosen specs (RAM, disk, OS)

View VM status + embedded terminal

View performance metrics (CPU/RAM usage chart per VM)

Receive alerts (simulated) for high usage or failed login attempts

👨‍💼 Admin Role

Access /admin dashboard

See all users and VMs

Stop/destroy any VM

Adjust user credits

View overall host monitoring (CPU load, RAM usage, disk space, network)

View SOC feed (aggregated logs of VM start/stop, login attempts, etc.)

🔎 4. Core Features Breakdown
Feature	Description	Tools
User Auth	Signup/login with JWT	FastAPI + passlib
VM Orchestration	Start/stop/destroy VMs using Vagrant	Vagrant + libvirt
Monitoring	System metrics dashboard	psutil + HTMX auto-refresh
SOC Feed	Aggregated logs of events	Python logging + SQLite
Web Terminal	Direct SSH access in browser	ttyd
Frontend UI	Modern, lightweight dashboard	Tailwind + HTMX + Alpine.js
Database	User, VM, and event tracking	SQLite (simple, fast)
🧠 5. System Architecture Diagram


Syntax error in text
mermaid version 11.6.0
📦 6. Directory Structure
twarga-cloud/
├── backend/
│   ├── main.py              # FastAPI app entry
│   ├── auth.py              # Login/Signup logic
│   ├── models.py            # SQLAlchemy ORM (User, VM, Event)
│   ├── schemas.py           # Pydantic models
│   ├── vm_manager.py        # Create/Destroy VMs via Vagrant
│   ├── monitor.py           # Host + VM metrics collector
│   ├── soc.py               # Security event feed + log parser
│   ├── database.py          # DB connection
│   └── utils.py             # Shared helpers
├── frontend/
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── admin.html
│   │   ├── monitor.html
│   │   └── soc.html
│   └── static/
│       └── style.css
├── vms/                     # User-specific VM folders
│   ├── user123-vm1/
│   │   └── Vagrantfile
├── logs/
│   └── events.log           # SOC feed source
└── README.md
🔬 7. Monitoring and SOC Integration
🧭 Host Monitoring

Collect metrics using psutil every 5 seconds:

CPU usage %

Memory %

Disk %

Network throughput

Expose /monitor endpoint → live dashboard refresh via HTMX

Optional: display chart via Chart.js (static embedded)

🧱 VM Monitoring

Each VM folder contains a .vm_info JSON file storing:

Name, status, RAM, IP, uptime

Periodically updated from vagrant status output

🛡️ SOC Feed

Collect logs from:

Vagrant lifecycle (created/stopped)

SSH login attempts (auth.log)

Store them in events table:

id | type | message | timestamp | vm_id

Display real-time in /soc dashboard:

e.g., “User twarga created VM ubuntu-test (512MB)”

e.g., “Failed SSH login detected on user123-vm1”

⚙️ 8. System Workflow

User logs in (JWT)

User dashboard shows:

Available credits

Active VMs (with metrics)

Launch form

When VM is launched:

vm_manager.py creates folder and Vagrantfile

subprocess starts vagrant up

System fetches IP via vagrant ssh-config

Starts ttyd bound to that IP

Logs event → SOC feed

/monitor page fetches system and VM metrics via psutil

/soc page lists all recent events in descending order

🧭 9. MVP Roadmap (Execution Plan)
🕐 Day 1 – Foundation

Initialize FastAPI app + templates

Implement login/signup (SQLite)

Create base dashboard layout (HTMX)

🕐 Day 2 – VM Lifecycle

Add vm_manager.py with create/start/stop

Store VM metadata in DB

Simple form to launch VM

🕐 Day 3 – Monitoring

Integrate psutil for system monitoring

Add /monitor endpoint + live refresh every 5s

Display system resource usage

🕐 Day 4 – SOC Feed

Create soc.py for event logging

Store and display VM lifecycle + SSH login logs

Add /soc route + feed UI

🕐 Day 5 – Admin Dashboard

Build /admin with all users, credits, and VM overview

Add “Stop” and “Delete” buttons for each VM

🕐 Day 6 – Web Terminal

Integrate ttyd

Embed iframe in user dashboard for VM access

🕐 Day 7 – Polish + Docs

Add styling, README, and screenshots

Add background task for periodic cleanup and metric update

🧭 10. Example SOC Dashboard (HTMX Live Feed)
<div id="soc-feed" hx-get="/soc/feed" hx-trigger="every 3s">
  <div class="border p-2 mb-1 bg-surface2">
    [17:22:03] INFO — user 'youness' created VM 'test-ubuntu'
  </div>
  <div class="border p-2 mb-1 bg-surface2">
    [17:24:12] ALERT — failed SSH login on vm 'test-ubuntu'
  </div>
</div>
🧠 11. Why This Works as a Lab
Area	What You Learn
Cloud Infrastructure	Simulating real-world cloud orchestration (KVM + API + dashboard)
Monitoring	Building a metrics + alerting system like Grafana but simpler
Security Operations	Collecting events, correlating activity, detecting suspicious SSH attempts
Automation	Lifecycle management using Vagrant subprocess control
Visualization	Live dashboards powered by HTMX auto-refresh and Tailwind
🧩 12. Next Phases (After MVP)
Version	Feature	Description
v0.2	Alerts & Notifications	Email or webhook alerts for incidents
v0.3	Multi-node support	Launch VMs on remote Proxmox host
v0.4	Container integration	Add Docker container simulation
v0.5	SIEM Export	Forward events to external Elastic/Splunk
v1.0	Public Demo	Publish on twarga.tech as open-source showcase

Would you like me to generate a Mermaid architecture diagram image (for your README.md) + Phase 1–2 FastAPI starter code (auth + dashboard + VM stub) next?
That would give you a running skeleton to start the lab tomorrow.
