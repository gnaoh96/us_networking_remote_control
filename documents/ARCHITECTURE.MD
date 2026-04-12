# Remote PC Control — Implementation Plan
*(Mid-Term Milestone — Local-First Build)*

> Docker packaging and Cloudflare public access are intentionally deferred to the final milestone. Everything here runs locally.

---

## Overview

A two-layer remote control application. The Mac hosts a Streamlit UI that uses **SSH (paramiko)** to run commands on a Windows 11 VM over UTM's local virtual network.

```
[Browser on Mac]
       |
       |  HTTP localhost:8501
       v
[Mac: Streamlit UI]
       |  SSH via paramiko
       v
[Windows VM: OpenSSH Server]
```

---

## Technology Stack

| Component | Technology |
| :--- | :--- |
| Virtualization | UTM (Shared Network mode) |
| VM OS | Windows 11 ARM — OpenSSH Server (built-in) |
| Remote Commands | `paramiko` SSH client on Mac |
| Process Control | `tasklist`, `taskkill` via SSH |
| Screenshot | PowerShell `CopyFromScreen` → SFTP back to Mac |
| Keylogger | `pynput` timed dump → SFTP log file back to Mac |
| File Transfer | `paramiko.SFTPClient` |
| Frontend UI | Streamlit (run directly, no Docker) |
| UI Auth | `st.session_state` password check (env var) |
| Testing | `pytest` + `unittest.mock` |
| Docker | ⏳ Deferred to final milestone |
| Cloudflare Tunnel | ⏳ Deferred to final milestone |
| Screen Recording [7] | `ffmpeg` on VM via SSH → SFTP `.mp4` back to Mac |

---

## Project Structure

```
remote-control/
├── app/
│   ├── main.py             # Streamlit UI
│   ├── ssh_client.py       # paramiko SSH helpers
│   └── config.py           # loads .env variables
├── tests/
│   └── test_ssh_client.py
├── .env.example            # documents required env vars
├── .gitignore              # exclude .venv/, .env, __pycache__/
├── requirements.txt
└── README.md
```

### requirements.txt
```
streamlit
paramiko
python-dotenv
pynput
pytest
```

### .env.example
```
VM_HOST=192.168.x.x
VM_USER=your_windows_username
VM_KEY_PATH=~/.ssh/id_rsa
APP_PASSWORD=your_ui_password
```

> Copy `.env.example` to `.env` and fill in your values. SSH uses key-based auth; `APP_PASSWORD` protects the Streamlit UI.

---

## Execution Plan

### Phase 1 — Infrastructure Setup (~2 hrs)

1. Download UTM → CrystalFetch → install Windows 11 ARM VM (≥4 GB RAM, ≥2 CPU cores).
2. Install UTM Guest Tools inside the VM.
3. Enable OpenSSH Server: **Windows Settings → Optional Features → OpenSSH Server → Install**.
4. **Start the SSH service and set it to auto-start** (run in PowerShell as Administrator on the VM):
   ```powershell
   Start-Service sshd
   Set-Service -Name sshd -StartupType Automatic
   ```
5. **Open port 22 in Windows Firewall** (PowerShell as Administrator on the VM):
   ```powershell
   New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
   ```
6. Run `ipconfig` in CMD → note the VM's IPv4 address.
7. Generate SSH key pair on Mac (ed25519 — stronger than RSA):
   ```bash
   ssh-keygen -t ed25519 -C "mac-to-vm"
   ```
   Copy the public key to the VM:
   ```bash
   ssh-copy-id <user>@<vm-ip>
   ```
   Or manually append `~/.ssh/id_ed25519.pub` to `C:\Users\<user>\.ssh\authorized_keys` on the VM.
8. Verify from Mac: `ssh <user>@<vm-ip>` — confirm passwordless login works.

### Phase 2 — Mac Client Setup (~0.5 hrs)

> **Prerequisite**: Ensure Python ≥ 3.9 is installed: `python3 --version`

1. Create the project folder structure:
   ```bash
   mkdir -p remote-control/app remote-control/tests
   ```
   Then create the files listed in the Project Structure section above.
2. Copy `.env.example` to `.env`, fill in `VM_HOST`, `VM_USER`, `VM_KEY_PATH`.
3. **Create a Python virtual environment** to isolate project dependencies from the system Python:
   ```bash
   python3 -m venv .venv
   ```
4. **Activate the virtual environment**:
   ```bash
   # macOS / Linux
   source .venv/bin/activate

   # Windows (if running from the VM side)
   .venv\Scripts\activate
   ```
   Your terminal prompt should now be prefixed with `(.venv)`.
5. Upgrade pip to avoid install failures:
   ```bash
   pip install --upgrade pip
   ```
6. Install dependencies inside the activated venv:
   ```bash
   pip install -r requirements.txt
   ```
7. Confirm Streamlit runs: `streamlit run app/main.py`

> **Tip**: Add both `.venv/` and `.env` to your `.gitignore` — secrets and the virtual environment should never be committed.

### Phase 3 — Development Sprints

#### Sprint 0 — Tests First (~1 hr)
- **Define the `ssh_client.py` public API first** (function signatures only, no implementation):
  - `connect(host, user, key_path) -> SSHClient`
  - `run_command(client, cmd) -> str`
  - `list_processes(client) -> list[dict]`
  - `kill_process(client, name) -> bool`
  - `screenshot(client) -> str`        # returns remote path `C:\Temp\screenshot.png`
  - `keylog(client, duration_sec) -> str` # returns remote path `C:\Temp\keylog.txt`
  - `start_recording(client) -> None`
  - `stop_recording(client) -> str`    # returns remote path `C:\Temp\recording.mp4`
  - `sftp_download(client, remote, local) -> None`
  - `sftp_upload(client, local, remote) -> None`
- Write `pytest` unit tests in `tests/test_ssh_client.py` using `unittest.mock` to mock paramiko against the API above, before any implementation.
- Run: `pytest tests/ -v`

#### Sprint 1 — Auth + Handshake (~1 hr)
- **Simple session-state password gate** — replace `streamlit-authenticator` with:
  ```python
  if not st.session_state.get("authed"):
      pwd = st.text_input("Password", type="password")
      if pwd == os.getenv("APP_PASSWORD"):
          st.session_state.authed = True
      st.stop()
  ```
- Implement `ssh_client.py`: connect via paramiko using key-based auth, run `hostname`.
- Streamlit: show VM online/offline indicator, display hostname on successful connect.
- Add SSH reconnection wrapper to handle dropped connections gracefully.

#### Sprint 2 — Process Management (~1.5 hrs)
**Covers requirements: [1][2] List/Kill processes & apps, [6] Shutdown/Reset**

> **Simplification**: apps and processes are the same thing on Windows. One unified process table covers both [1] and [2].

Via `paramiko.exec_command()` (all commands run **remotely on the VM**):

- List processes: `tasklist` → parse into a structured table (Name, PID, Memory) with per-row **Kill** button.
- Kill process/app: `taskkill /IM <name> /F`
- Shutdown: `shutdown /s /t 0`
- Restart: `shutdown /r /t 0`

#### Sprint 3 — Screenshot & Keylogger (~2 hrs)
**Covers requirements: [3] Chụp màn hình, [4] Bắt phím nhấn**

- **Screenshot**:
  - Run a PowerShell one-liner on the VM to capture the screen and save to a temp file:
    ```powershell
    Add-Type -AssemblyName System.Windows.Forms;
    $b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;
    $bmp=New-Object System.Drawing.Bitmap $b.Width,$b.Height;
    $g=[System.Drawing.Graphics]::FromImage($bmp);
    $g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size);
    $bmp.Save('C:\Temp\screenshot.png')
    ```
  - SFTP the saved file back to Mac → display in Streamlit with `st.image()`.
  - Add a "Refresh" button for on-demand capture.

- **Keylogger** (file-dump pattern — no streaming complexity):
  - **Prerequisite**: install `pynput` on the Windows VM:
    ```
    pip install pynput
    ```
  - Run a timed pynput script on the VM via SSH for a fixed duration (e.g. 30 sec); output written to `C:\Temp\keylog.txt`.
  - SFTP `C:\Temp\keylog.txt` back to Mac → display in Streamlit as plain text.
  - No persistent channel needed — same simple pattern as screenshot.
  - For demo/educational use only — document this clearly in README.

#### Sprint 4 — File Transfer (~1 hr)
**Covers requirement: [5] Copy Files**

- **Upload** (Mac → VM): Streamlit `st.file_uploader` → SFTP to fixed path `C:\Temp\<filename>`.
- **Download** (VM → Mac): text input for filename → SFTP from `C:\Temp\<filename>` → `st.download_button`.
- No directory browsing or progress bars for mid-term — keep it simple.

#### Sprint 5 — Screen Recording & Polish (~1.5 hrs)
**Covers requirement: [7] Start Webcam; Record → implemented as screen recording**

> **Design choice**: Instead of live webcam streaming (requires OpenCV + WebRTC — high complexity), requirement [7] is fulfilled as **screen recording**: start recording on the VM, stop it, and return the `.mp4` file via SFTP. Same SSH+SFTP pattern as screenshot — no new transport layer needed.

- **Prerequisite**: install `ffmpeg` on the Windows VM:
  ```
  winget install ffmpeg
  ```
  Verify: `ffmpeg -version`

- **Start recording** via SSH:
  ```powershell
  Start-Process -NoNewWindow ffmpeg -ArgumentList '-f gdigrab -framerate 25 -i desktop C:\Temp\recording.mp4'
  ```
  Store the process PID in `st.session_state` for later termination.

- **Stop recording** via SSH (graceful quit signal to ffmpeg):
  ```powershell
  taskkill /IM ffmpeg.exe /F
  ```

- **Return file**: SFTP `C:\Temp\recording.mp4` back to Mac → offer `st.download_button()` in Streamlit.

- **Streamlit UI**: Start / Stop buttons with recording indicator (elapsed timer). Show file size and download link after stop.

- **Caveats to document in README**:
  - File size grows with duration — recommend a max recording time (e.g. 2 min) enforced by a timer.
  - Graceful stop via `taskkill /F` may cut the last frame; a named pipe signal is cleaner but out of scope.

- Clean up UI layout: group features into tabs (Processes / Capture / Keylogger / Files / System).
- Ensure all error states are handled (SSH drop, auth fail, command timeout, ffmpeg not found).
- Run full `pytest` suite, confirm all mocked tests pass.
- Prepare demo script: login → view processes → kill one → screenshot → keylog → upload file → start + stop recording → download video → shutdown.

---

## Agent Implementation Notes

> Read this section before generating any code.

- **Entry point** is `app/main.py` (Streamlit). Do not create a separate Flask or FastAPI server.
- **All VM interaction** must go through `ssh_client.py`. Never call `paramiko` directly from `main.py`.
- **Credentials** are loaded via `config.py` using `python-dotenv`. Never hardcode IPs, usernames, or key paths.
- **SSH auth** is key-based only. Do not implement password auth.
- **UI auth** is a simple `st.session_state` password check against `APP_PASSWORD` env var. Do not use `streamlit-authenticator`.
- **Tests** mock paramiko at the `ssh_client` boundary. Do not write tests that require a live VM.
- **All VM-side output** (screenshots, keylogs, recordings) is written to `C:\Temp\` — never prompt the user for paths.
- **Keylogger** runs a timed dump (not a streaming channel). Run for fixed duration → write file → SFTP back.
- **Screen recording** uses `ffmpeg` on the VM. Track state in `st.session_state`; always stop before session ends.
- **No Docker** at this stage. Run with `streamlit run app/main.py` directly.

---

## Quick Reference

| Task | Command |
| :--- | :--- |
| Create venv | `python3 -m venv .venv` |
| Activate venv (Mac/Linux) | `source .venv/bin/activate` |
| Deactivate venv | `deactivate` |
| Install dependencies | `pip install -r requirements.txt` |
| Start app (local) | `streamlit run app/main.py` |
| Run tests | `pytest tests/ -v` |
| Check VM IP | `ipconfig` in Windows CMD |
| SSH into VM | `ssh <user>@<vm-ip>` |
| Copy SSH key to VM | `ssh-copy-id <user>@<vm-ip>` |

---

## Future Milestone — Docker & Public Access

Deferred items to add once the local build is stable:

| Item | Notes |
| :--- | :--- |
| `Dockerfile` | `FROM python:3.11-slim`, `EXPOSE 8501`, run Streamlit on `0.0.0.0` |
| `docker-compose.yml` | Mounts `.env`, maps port 8501 |
| Cloudflare quick tunnel | `cloudflared tunnel --url http://localhost:8501` — no account needed, great for demos |
| Cloudflare persistent tunnel | Requires free account; gives stable URL across restarts |

---

## Scope Boundaries

| Included (Mid-Term) | Excluded / Deferred |
| :--- | :--- |
| [1][2] Unified process list + kill | App *start* (UX complexity, out of scope) |
| [3] Screenshot (PowerShell + SFTP) | Live webcam streaming (final milestone) |
| [4] Keylogger (timed file dump) | Streaming keylog (final milestone) |
| [5] File upload/download (fixed path) | Directory browsing + progress bars |
| [6] Shutdown / Restart | Docker packaging (final milestone) |
| [7] Screen recording (ffmpeg + SFTP) | Cloudflare public URL (final milestone) |
| Session-state password gate | `streamlit-authenticator` (removed) |
| SSH key-based auth | Multi-VM orchestration |
| `pytest` + mock test suite | Production key rotation |