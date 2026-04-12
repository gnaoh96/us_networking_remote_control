# 🖥️ Remote PC Control

A browser-based tool to remotely manage **two Windows 11 VMs** from a Mac host — using SSH/SFTP as the sole transport layer, with no agents or third-party remote-desktop software required.

> **Midterm Milestone** — Sprint 0–4 complete.

---

## How It Works

```
Mac (Streamlit UI at localhost:8501)
         │
         │  SSH + SFTP  (Ed25519 key auth)
         ▼
 ┌───────────────┐    ┌───────────────┐
 │   VM 1        │    │   VM 2        │
 │ 192.168.64.2  │    │ 192.168.64.4  │
 │ OpenSSH :22   │    │ OpenSSH :22   │
 └───────────────┘    └───────────────┘
         │
         └── C:\Temp\   (all files land here)
         └── Task Scheduler  (bridges Session 0 → Session 1)
```

**Session 0 isolation** is the key challenge: SSH processes run in Windows Session 0 (no display). Any GUI-dependent operation (screenshot, keyboard capture) must be delegated to Session 1 via a Scheduled Task with `LogonType=Interactive`. A VBScript wrapper ensures no CMD/PowerShell windows appear on the VM desktop.

---

## Multi-VM Operation

The sidebar shows both VMs simultaneously. You can:
- **Connect / Disconnect** each VM independently
- **Switch the active VM** with a radio selector — all tabs (Processes, Screenshot, Keylogger, Files, System) instantly target the selected VM
- Both VMs share the same SSH key (`~/.ssh/id_ed25519`)

```ini
# .env
VM1_HOST = "192.168.64.2"
VM1_USER = "vm1"
VM2_HOST = "192.168.64.4"
VM2_USER = "vm1"
VM_KEY_PATH  = "~/.ssh/id_ed25519"
APP_PASSWORD = "your_password"
```

---

## Features

### ⚙️ Process Manager
- Lists all running processes (`tasklist /FO CSV`) — searchable, filterable
- **Kill** any process by name (`taskkill /IM name /F`)
- **Launch** any app (e.g. `notepad.exe`) — runs via Scheduled Task in Session 1 so it appears on the VM's visible desktop

### 📸 Screenshot
- Captures the VM's real desktop using `CopyFromScreen` (PowerShell + `System.Windows.Forms`)
- Runs silently via: `Task → wscript.exe → powershell -WindowStyle Hidden`
- Returns a PNG viewable and downloadable in the browser

### ⌨️ Keylogger
- Records all keystrokes on the VM for a configurable duration (5–60 s)
- `pynput` runs via: `Task → wscript.exe → python.exe` (all hidden, blocking)
- Full path to `python.exe` resolved at runtime to bypass Task Scheduler's PATH
- Returns a plain-text log, downloadable

### 📁 File Transfer
- **Upload** any file from Mac → `C:\Temp\<name>` on VM via SFTP
- **Download** any file from `C:\Temp\` on VM → browser save dialog

### 🔴 System Controls
- Remote **Shutdown** and **Restart** with two-click confirmation
- Uses `shutdown /s /t 0` / `shutdown /r /t 0`

---

## Setup

```bash
# 1. Create venv and install deps
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Copy and fill .env
cp .env.example .env   # set VM1_HOST, VM2_HOST, VM_KEY_PATH, APP_PASSWORD

# 3. Run
streamlit run app/main.py
```

**VM requirements:** OpenSSH Server enabled, Mac's `id_ed25519.pub` in `authorized_keys`, `pynput` installed (`pip install pynput`).

---

## Project Layout

```
app/
├── main.py        # Streamlit UI — auth, sidebar, all tabs
├── ssh_client.py  # All SSH/SFTP logic (paramiko, no UI)
└── config.py      # Loads .env → VMS list + constants
requirements.txt   # streamlit, paramiko, python-dotenv, pynput
```

---

## Known Limitations

| Item | Note |
|---|---|
| Screenshot ~8 s | Task Scheduler startup overhead |
| Keylogger `duration + ~10 s` | Task start delay + flush buffer |
<!-- | Screen recording | Removed; redesigning for final milestone |
| Single shared SSH key | Both VMs must accept `id_ed25519` | -->
