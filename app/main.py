"""
main.py — Streamlit UI for Remote PC Control.
Entry point: streamlit run app/main.py
"""
import os
import sys
import time
import tempfile

import streamlit as st

# Allow running from repo root or from app/
sys.path.insert(0, os.path.dirname(__file__))

import config
import ssh_client as sc

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Remote PC Control",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark gradient background */
.stApp {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    min-height: 100vh;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%);
    border-right: 1px solid rgba(99,102,241,0.2);
}

/* Cards */
.metric-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
    backdrop-filter: blur(10px);
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: rgba(99,102,241,0.6); }

/* Status badge */
.badge-online  { color: #22c55e; font-weight: 600; font-size: 0.85rem; }
.badge-offline { color: #ef4444; font-weight: 600; font-size: 0.85rem; }

/* Section headers */
.section-title {
    color: #a5b4fc;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
    margin-top: 1.2rem;
}

/* Login card */
.login-wrap {
    max-width: 420px;
    margin: 6rem auto 0;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 20px;
    padding: 2.5rem;
    backdrop-filter: blur(12px);
}

/* Tab styling */
[data-testid="stTabs"] button {
    font-size: 0.85rem;
    font-weight: 500;
    color: #94a3b8;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #a5b4fc;
    border-bottom-color: #6366f1 !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}

/* Hide Streamlit branding */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# AUTH GATE
# ─────────────────────────────────────────────────────────────────────────────
def auth_gate():
    st.markdown("""
    <div class='login-wrap'>
        <h2 style='color:#a5b4fc;margin:0 0 0.3rem;font-size:1.6rem;'>🖥️ Remote PC Control</h2>
        <p style='color:#64748b;margin:0 0 1.8rem;font-size:0.9rem;'>Enter your access password to continue.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br><br><br><br><br>", unsafe_allow_html=True)
        with st.form("login_form"):
            pwd = st.text_input("Password", type="password",
                                placeholder="Enter access password…")
            submitted = st.form_submit_button(
                "Sign In →", use_container_width=True, type="primary"
            )
            if submitted:
                if pwd == config.APP_PASSWORD:
                    st.session_state.authed = True
                    st.rerun()
                else:
                    st.error("❌ Incorrect password.")


if not st.session_state.get("authed"):
    auth_gate()
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# SSH CONNECTION MANAGEMENT
# ─────────────────────────────────────────────────────────────────────────────
def get_client(vm_id: str):
    """Return the live SSH client for a specific VM, or None."""
    return st.session_state.get(f"ssh_{vm_id}")


def connect_vm(vm: dict):
    """Open an SSH connection to vm and store it in session_state."""
    try:
        client = sc.connect(vm["host"], vm["user"], config.VM_KEY_PATH)
        st.session_state[f"ssh_{vm['id']}"] = client
        st.session_state.pop(f"err_{vm['id']}", None)
    except Exception as e:
        st.session_state[f"ssh_{vm['id']}"] = None
        st.session_state[f"err_{vm['id']}"] = str(e)


def disconnect_vm(vm_id: str):
    """Close and remove the SSH connection for a VM."""
    cli = st.session_state.get(f"ssh_{vm_id}")
    if cli:
        try:
            cli.close()
        except Exception:
            pass
    st.session_state.pop(f"ssh_{vm_id}", None)
    st.session_state.pop(f"err_{vm_id}", None)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🖥️ Remote Control")
    st.markdown("---")

    # ── Per-VM status cards + connect/disconnect ────────────────────────────────
    for vm in config.VMS:
        vm_id  = vm["id"]
        cli    = get_client(vm_id)
        online = sc.is_connected(cli)
        color  = "#22c55e" if online else "#ef4444"
        dot    = "● Connected" if online else "● Disconnected"

        st.markdown(
            f"<div class='metric-card'>"
            f"  <div style='color:#64748b;font-size:0.72rem;font-weight:600;'>{vm['label'].upper()}</div>"
            f"  <div style='color:#e2e8f0;font-size:0.88rem;font-weight:600;margin-top:0.15rem;'>"
            f"    {vm['user']}@{vm['host']}"
            f"  </div>"
            f"  <div style='color:{color};font-size:0.8rem;margin-top:0.2rem;'>{dot}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        if not online:
            if st.button(f"⚡ Connect {vm['label']}",
                         key=f"btn_con_{vm_id}",
                         use_container_width=True, type="primary"):
                with st.spinner(f"Connecting to {vm['label']}…"):
                    connect_vm(vm)
                st.rerun()
            if err := st.session_state.get(f"err_{vm_id}"):
                st.error("Connection failed")
                with st.expander("🔍 Debug info"):
                    st.code(
                        f"Host : {vm['host']}\nUser : {vm['user']}\n"
                        f"Key  : {config.VM_KEY_PATH}",
                        language=None,
                    )
        else:
            try:
                hn = sc.run_command(cli, "hostname")
                st.markdown(
                    f"<div style='color:#22c55e;font-size:0.75rem;padding:0 0.2rem 0.4rem;'>"
                    f"Host: {hn}</div>",
                    unsafe_allow_html=True,
                )
            except Exception:
                pass
            if st.button(f"🔌 Disconnect {vm['label']}",
                         key=f"btn_dis_{vm_id}",
                         use_container_width=True):
                disconnect_vm(vm_id)
                if st.session_state.get("active_vm_id") == vm_id:
                    st.session_state.pop("active_vm_id", None)
                st.rerun()

    # ── Active VM selector (only when ≥1 VM is connected) ───────────────────
    connected_vms = [vm for vm in config.VMS if sc.is_connected(get_client(vm["id"]))]
    if connected_vms:
        st.markdown("---")
        st.markdown("<div class='section-title'>Active VM — Tabs</div>",
                    unsafe_allow_html=True)

        current_id = st.session_state.get("active_vm_id",
                                           connected_vms[0]["id"])
        # If the previously-active VM just disconnected, fall back to first
        if current_id not in [v["id"] for v in connected_vms]:
            current_id = connected_vms[0]["id"]

        chosen_id = st.radio(
            "active_vm_radio",
            options=[vm["id"] for vm in connected_vms],
            format_func=lambda x: next(v["label"] for v in connected_vms if v["id"] == x),
            index=[vm["id"] for vm in connected_vms].index(current_id),
            label_visibility="collapsed",
            key="vm_radio",
        )
        st.session_state["active_vm_id"] = chosen_id

    st.markdown("---")
    st.markdown("<div class='section-title'>Session</div>", unsafe_allow_html=True)
    if st.button("🔒 Sign Out", use_container_width=True):
        for vm in config.VMS:
            disconnect_vm(vm["id"])
        st.session_state.clear()
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<div style='color:#334155;font-size:0.7rem;text-align:center;'>"
        "Remote Control v0.2 · Local Build</div>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("# 🖥️ Remote PC Control")

connected_vms = [vm for vm in config.VMS if sc.is_connected(get_client(vm["id"]))]
active_vm_id  = st.session_state.get("active_vm_id")

if not connected_vms or not active_vm_id:
    st.markdown("""
    <div class='metric-card' style='text-align:center;padding:2.5rem;'>
        <div style='font-size:3rem;'>🔌</div>
        <div style='color:#94a3b8;margin-top:0.8rem;font-size:1rem;'>
            Not connected to any VM.<br>
            Click <strong style='color:#a5b4fc;'>⚡ Connect</strong> in the sidebar to start.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Resolve active VM config + client
active_vm = next(vm for vm in config.VMS if vm["id"] == active_vm_id)
client    = get_client(active_vm_id)

# Show which VM the tabs are operating on
st.markdown(
    f"<div style='color:#64748b;font-size:0.82rem;margin-bottom:0.2rem;'>"
    f"Controlling: <strong style='color:#a5b4fc;'>{active_vm['label']}</strong>"
    f" — {active_vm['user']}@{active_vm['host']}"
    f"</div>",
    unsafe_allow_html=True,
)

# Clear tab caches when the user switches VMs so stale data doesn't bleed over
_prev_vm = st.session_state.get("_prev_active_vm")
if _prev_vm != active_vm_id:
    for _k in ["proc_list", "screenshot_bytes", "screenshot_ts",
               "keylog_text", "keylog_ts"]:
        st.session_state.pop(_k, None)
    st.session_state["_prev_active_vm"] = active_vm_id

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_proc, tab_capture, tab_keylog, tab_files, tab_system = st.tabs([
    "⚙️ Processes",
    "📸 Screenshot",
    "⌨️ Keylogger",
    "📁 Files",
    "🔴 System",
])



# ── TAB 1: Processes ──────────────────────────────────────────────────────────
with tab_proc:
    st.markdown("### ⚙️ Process Manager")

    # ── Launch App (top) ──────────────────────────────────────────────────────
    with st.expander("🚀 Launch Application / Process", expanded=True):
        st.caption(
            "Start any app on the VM's desktop. Use the exe name or a full path. "
            "The process will appear on the VM's visible screen."
        )
        col_exe, col_btn = st.columns([4, 1])
        with col_exe:
            exe_input = st.text_input(
                "Executable",
                placeholder="e.g. notepad.exe  or  C:\\Windows\\System32\\calc.exe",
                key="launch_exe",
                label_visibility="collapsed",
            )
        with col_btn:
            launch_clicked = st.button(
                "▶️ Launch", type="primary",
                use_container_width=True, key="btn_launch"
            )

        if launch_clicked:
            if not exe_input.strip():
                st.warning("⚠️ Enter an executable name or path first.")
            else:
                with st.spinner(f"Launching `{exe_input}` on the VM (~5 s)…"):
                    try:
                        ok, msg = sc.start_process(client, exe_input.strip())
                        if ok:
                            st.success(f"✅ {msg}")
                            st.session_state.pop("proc_list", None)  # auto-refresh list
                        else:
                            st.warning(f"⚠️ {msg}")
                    except Exception as e:
                        st.error(f"❌ Launch failed: {e}")

    st.markdown("")
    st.caption("Lists all running processes on the VM. Use Kill to terminate by name.")

    col_r, col_k = st.columns([3, 1])

    with col_r:
        if st.button("🔄 Refresh Processes", key="refresh_proc"):
            st.session_state.pop("proc_list", None)

    if "proc_list" not in st.session_state:
        with st.spinner("Fetching processes…"):
            try:
                st.session_state.proc_list = sc.list_processes(client)
            except Exception as e:
                st.error(f"Failed to list processes: {e}")
                st.session_state.proc_list = []

    procs = st.session_state.get("proc_list", [])

    if procs:
        st.markdown(f"<div style='color:#64748b;font-size:0.8rem;'>{len(procs)} processes running</div>",
                    unsafe_allow_html=True)

        # Search filter
        search = st.text_input("🔍 Filter by name", placeholder="e.g. chrome.exe", key="proc_search")
        filtered = [p for p in procs if search.lower() in p["name"].lower()] if search else procs

        import pandas as pd
        if not filtered:
            st.info(f"🔍 No processes found matching **\"{search}\"**.")
        else:
            df = pd.DataFrame(filtered)[["name", "pid", "mem_kb", "session"]]
            df.columns = ["Process Name", "PID", "Memory (KB)", "Session"]
            st.dataframe(df, use_container_width=True, hide_index=True, height=380)

        st.markdown("---")
        st.markdown("#### Kill a Process")
        col_a, col_b = st.columns([3, 1])
        with col_a:
            kill_name = st.text_input("Process name to kill", placeholder="e.g. notepad.exe", key="kill_name")
        with col_b:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💀 Kill", type="primary", use_container_width=True):
                if kill_name:
                    with st.spinner(f"Killing {kill_name}…"):
                        ok, msg = sc.kill_process(client, kill_name)
                    if ok:
                        st.success(f"✅ {kill_name} terminated.")
                        st.session_state.pop("proc_list", None)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
                else:
                    st.warning("Enter a process name first.")


# ── TAB 2: Screenshot ─────────────────────────────────────────────────────────
with tab_capture:
    st.markdown("### 📸 Screenshot")
    st.caption("Captures the VM screen and displays it here.")

    if st.button("📸 Take Screenshot", type="primary", key="btn_screenshot"):
        with st.spinner("Capturing screen…"):
            try:
                img_bytes = sc.screenshot(client)
                st.session_state.screenshot_bytes = img_bytes
                st.session_state.screenshot_ts = time.strftime("%H:%M:%S")
            except Exception as e:
                st.error(f"Screenshot failed: {e}")

    if img := st.session_state.get("screenshot_bytes"):
        ts = st.session_state.get("screenshot_ts", "")
        st.caption(f"Captured at {ts}")
        st.image(img, use_container_width=True)
        st.download_button(
            "⬇️ Download PNG",
            data=img,
            file_name=f"screenshot_{ts.replace(':','-')}.png",
            mime="image/png",
        )


# ── TAB 3: Keylogger ─────────────────────────────────────────────────────────
with tab_keylog:
    st.markdown("### ⌨️ Keylogger")
    st.caption(
        "Runs a timed keylogger on the VM and returns the captured keystrokes as a text file. "
        "**For demo/educational use only.**"
    )
    # st.warning("⚠️ Requires `pynput` installed on the Windows VM: `pip install pynput`")

    duration = st.slider("Capture duration (seconds)", min_value=5, max_value=60, value=15, step=5)

    if st.button("▶️ Start Keylog Capture", type="primary", key="btn_keylog"):
        with st.spinner(f"Capturing keystrokes for {duration} seconds… (do not close this page)"):
            try:
                log_text = sc.keylog(client, duration_sec=duration)
                st.session_state.keylog_text = log_text
                st.session_state.keylog_ts = time.strftime("%H:%M:%S")
            except Exception as e:
                st.error(f"Keylog failed: {e}")

    if log := st.session_state.get("keylog_text"):
        ts = st.session_state.get("keylog_ts", "")
        st.caption(f"Captured at {ts}")
        st.code(log if log.strip() else "(no keystrokes detected)", language=None)
        st.download_button(
            "⬇️ Download log",
            data=log,
            file_name=f"keylog_{ts.replace(':','-')}.txt",
            mime="text/plain",
        )


# ── TAB 4: File Transfer ─────────────────────────────────────────────────────
with tab_files:
    st.markdown("### 📁 File Transfer")
    st.caption("All files are transferred to/from `C:\\Temp\\` on the VM.")

    col_up, col_dn = st.columns(2)

    with col_up:
        st.markdown("#### ⬆️ Upload (Mac → VM)")
        uploaded = st.file_uploader("Choose a file to upload", key="file_upload")
        if st.button("Upload to VM", type="primary", key="btn_upload", disabled=not uploaded):
            with st.spinner(f"Uploading {uploaded.name}…"):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded.name) as tmp:
                        tmp.write(uploaded.read())
                        tmp_path = tmp.name
                    sc.sftp_upload_file(client, tmp_path, uploaded.name)
                    os.unlink(tmp_path)
                    st.success(f"✅ Uploaded to `C:\\Temp\\{uploaded.name}`")
                except Exception as e:
                    st.error(f"Upload failed: {e}")

    with col_dn:
        st.markdown("#### ⬇️ Download (VM → Mac)")
        dl_name = st.text_input("Filename in `C:\\Temp\\`", placeholder="e.g. output.txt", key="dl_name")
        if st.button("Download from VM", type="primary", key="btn_download", disabled=not dl_name):
            with st.spinner(f"Downloading {dl_name}…"):
                try:
                    data = sc.sftp_download_bytes(client, rf"C:\Temp\{dl_name}")
                    st.download_button(
                        f"⬇️ Save {dl_name}",
                        data=data,
                        file_name=dl_name,
                    )
                    st.success(f"✅ Ready to download.")
                except Exception as e:
                    st.error(f"Download failed: {e}")


# # ── TAB 5: Screen Recording ──────────────────────────────────────────────────
# with tab_record:
#     st.markdown("### 🎬 Screen Recording")
#     st.caption(
#         "Records the VM desktop using `ffmpeg`. Start → Stop → Download the `.mp4` file. "
#         "**Requires `ffmpeg` on the VM** — install via `winget install ffmpeg`."
#     )
#     st.warning("⚠️ Requires `ffmpeg` installed on the Windows VM.")

#     is_recording = st.session_state.get("recording", False)

#     col_s, col_e = st.columns(2)
#     with col_s:
#         if st.button("⏺ Start Recording", type="primary",
#                      key="btn_rec_start", disabled=is_recording):
#             with st.spinner("Starting ffmpeg…"):
#                 try:
#                     sc.start_recording(client)
#                     st.session_state.recording = True
#                     st.session_state.recording_start = time.time()
#                     st.rerun()
#                 except Exception as e:
#                     st.error(f"Failed to start: {e}")

#     with col_e:
#         if st.button("⏹ Stop & Download", type="primary",
#                      key="btn_rec_stop", disabled=not is_recording):
#             with st.spinner("Stopping ffmpeg and fetching file…"):
#                 try:
#                     video_bytes = sc.stop_recording(client)
#                     st.session_state.recording = False
#                     st.session_state.recording_video = video_bytes
#                     st.session_state.recording_ts = time.strftime("%H:%M:%S")
#                     st.rerun()
#                 except Exception as e:
#                     st.error(f"Failed to stop: {e}")
#                     st.session_state.recording = False

#     if is_recording:
#         elapsed = int(time.time() - st.session_state.get("recording_start", time.time()))
#         st.markdown(
#             f"<div style='color:#ef4444;font-weight:600;font-size:0.9rem;'>"
#             f"🔴 Recording\u2026 {elapsed}s elapsed</div>",
#             unsafe_allow_html=True,
#         )
#         if elapsed > 120:
#             st.warning("⚠️ Recording over 2 minutes \u2014 consider stopping to keep file size manageable.")
#         # Refresh every second so the timer counts up live
#         time.sleep(1)
#         st.rerun()

#     if vid := st.session_state.get("recording_video"):
#         ts = st.session_state.get("recording_ts", "")
#         st.success(f"✅ Recording ready ({len(vid)//1024} KB)")
#         st.download_button(
#             "⬇️ Download recording.mp4",
#             data=vid,
#             file_name=f"recording_{ts.replace(':','-')}.mp4",
#             mime="video/mp4",
#         )


# ── TAB 6: System ─────────────────────────────────────────────────────────────
with tab_system:
    st.markdown("### 🔴 System Controls")
    st.caption("Shutdown or restart the Windows VM immediately.")

    st.error("⚠️ These actions are immediate and irreversible. The VM will shut down or restart right away.")

    col_sd, col_rs = st.columns(2)

    with col_sd:
        st.markdown("""
        <div class='metric-card' style='text-align:center;'>
            <div style='font-size:2.5rem;'>⏻</div>
            <div style='color:#e2e8f0;font-weight:600;margin:0.4rem 0;'>Shutdown</div>
            <div style='color:#64748b;font-size:0.8rem;'>Powers off the VM immediately</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⏻ Shutdown VM", use_container_width=True, key="btn_shutdown"):
            if st.session_state.get("confirm_shutdown"):
                with st.spinner("Sending shutdown command…"):
                    sc.shutdown(client)
                disconnect_vm()
                st.session_state.confirm_shutdown = False
                st.success("Shutdown command sent. VM will power off.")
            else:
                st.session_state.confirm_shutdown = True
                st.warning("Click **Shutdown VM** again to confirm.")

    with col_rs:
        st.markdown("""
        <div class='metric-card' style='text-align:center;'>
            <div style='font-size:2.5rem;'>🔄</div>
            <div style='color:#e2e8f0;font-weight:600;margin:0.4rem 0;'>Restart</div>
            <div style='color:#64748b;font-size:0.8rem;'>Reboots the VM immediately</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔄 Restart VM", use_container_width=True, key="btn_restart"):
            if st.session_state.get("confirm_restart"):
                with st.spinner("Sending restart command…"):
                    sc.restart(client)
                disconnect_vm()
                st.session_state.confirm_restart = False
                st.success("Restart command sent.")
            else:
                st.session_state.confirm_restart = True
                st.warning("Click **Restart VM** again to confirm.")
