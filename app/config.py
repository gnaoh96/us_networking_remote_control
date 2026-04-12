"""
config.py — loads .env into typed constants.
All other modules import from here; never read os.environ directly.

To add more VMs, add VM3_HOST / VM3_USER in .env and append
another entry to the _VM_DEFS list below.
"""
import os
from dotenv import load_dotenv

load_dotenv()

VM_KEY_PATH:  str = os.path.expanduser(os.getenv("VM_KEY_PATH", "~/.ssh/id_ed25519"))
APP_PASSWORD: str = os.getenv("APP_PASSWORD", "admin")

# ── VM registry ───────────────────────────────────────────────────────────────
# Add new VMs here. Any entry whose host is empty is silently skipped.
_VM_DEFS = [
    {"id": "vm1", "label": "VM 1", "host": os.getenv("VM1_HOST", ""), "user": os.getenv("VM1_USER", "")},
    {"id": "vm2", "label": "VM 2", "host": os.getenv("VM2_HOST", ""), "user": os.getenv("VM2_USER", "")},
]

# Only expose VMs that have a host configured
VMS: list[dict] = [vm for vm in _VM_DEFS if vm["host"]]
