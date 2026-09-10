"""
KrushiSetu Platform - Application Lifecycle Controller
Supports START, STOP, RESTART, and STATUS operations.

Usage:
    python run.py             # Default: Starts the server in foreground
    python run.py start       # Starts the server (supports --daemon for background)
    python run.py stop        # Stops any running server on port 8000
    python run.py restart     # Gracefully restarts the server
    python run.py status      # Displays live health and process status
"""

import os
import sys
import time
import argparse
import subprocess
import signal
import urllib.request
import json
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

PID_FILE = PROJECT_ROOT / ".krushisetu.pid"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000

# =============================================================================
# START SECTION
# =============================================================================
def start_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, reload: bool = True, daemon: bool = False):
    """
    START SECTION:
    Launches the KrushiSetu FastAPI / Uvicorn server.
    Supports foreground interactive mode and background daemon mode.
    """
    # Check if already running
    if is_port_in_use(host, port):
        print(f"[!] Server is already running on http://{host}:{port}")
        show_status(host, port)
        return

    print("================================================================")
    print("           KRUSHISETU PLATFORM - STARTING SERVER                ")
    print("================================================================")
    print(f"  Host           : http://{host}:{port}")
    print(f"  Portal URL     : http://{host}:{port}/pages/dashboard.html")
    print(f"  API Docs       : http://{host}:{port}/docs")
    print(f"  Health Check   : http://{host}:{port}/api/health")
    print(f"  Login Page     : http://{host}:{port}/pages/login.html")
    print(f"  Auto-Reload    : {'Enabled' if reload else 'Disabled'}")
    print(f"  Mode           : {'Background (Daemon)' if daemon else 'Interactive (Foreground)'}")
    print("================================================================")

    if daemon:
        # Launch background process
        cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", f"--host={host}", f"--port={port}"]
        if reload:
            cmd.append("--reload")
        
        proc = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
        )
        save_pid(proc.pid)
        print(f"[+] Server started in background with PID: {proc.pid}")
        time.sleep(1.5)
        show_status(host, port)
    else:
        # Foreground process
        save_pid(os.getpid())
        import uvicorn
        try:
            uvicorn.run("backend.main:app", host=host, port=port, reload=reload)
        finally:
            remove_pid()

# =============================================================================
# STOP SECTION
# =============================================================================
def stop_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """
    STOP SECTION:
    Gracefully stops the running KrushiSetu server.
    Terminates by PID file or by finding the process listening on port 8000.
    """
    print("================================================================")
    print("           KRUSHISETU PLATFORM - STOPPING SERVER                ")
    print("================================================================")

    stopped = False

    # 1. Try stopping via saved PID
    pid = get_saved_pid()
    if pid:
        print(f"[*] Found PID file with PID {pid}. Attempting termination...")
        if kill_pid(pid):
            print(f"[+] Successfully stopped process {pid}.")
            stopped = True
        remove_pid()

    # 2. Check if port is still occupied and kill process on port
    pids_on_port = find_pids_on_port(port)
    if pids_on_port:
        print(f"[*] Found process(es) listening on port {port}: {pids_on_port}")
        for p in pids_on_port:
            if kill_pid(p):
                print(f"[+] Terminated process {p} on port {port}.")
                stopped = True

    if stopped:
        print(f"[+] KrushiSetu server stopped successfully.")
    else:
        print(f"[i] No active KrushiSetu server found running on port {port}.")

# =============================================================================
# STATUS SECTION
# =============================================================================
def show_status(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """
    STATUS SECTION:
    Inspects server health, PID, and endpoint availability.
    """
    print("================================================================")
    print("           KRUSHISETU PLATFORM - SERVER STATUS                  ")
    print("================================================================")
    
    url = f"http://{host}:{port}/api/health"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KrushiSetu-CLI"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                print("  Status         : [ONLINE] Running Healthy")
                print(f"  URL            : http://{host}:{port}")
                print(f"  API Health     : {data.get('status', 'OK')}")
                print(f"  Database       : {data.get('database', 'Connected')}")
                print(f"  Environment    : {data.get('environment', 'Development')}")
                pids = find_pids_on_port(port)
                if pids:
                    print(f"  Active PID(s)  : {', '.join(map(str, pids))}")
                print("================================================================")
                return True
    except Exception:
        pass

    print("  Status         : [OFFLINE] Server is stopped")
    print(f"  Target Port    : {port}")
    print("================================================================")
    return False

# =============================================================================
# RESTART SECTION
# =============================================================================
def restart_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, reload: bool = True):
    """
    RESTART SECTION:
    Stops any active server instance and restarts a fresh instance.
    """
    print("================================================================")
    print("           KRUSHISETU PLATFORM - RESTARTING SERVER              ")
    print("================================================================")
    stop_server(host, port)
    time.sleep(1.0)
    start_server(host, port, reload=reload, daemon=False)

# =============================================================================
# HELPER UTILITIES
# =============================================================================
def is_port_in_use(host: str, port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def find_pids_on_port(port: int):
    pids = set()
    try:
        if sys.platform == "win32":
            output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, text=True, stderr=subprocess.DEVNULL)
            for line in output.strip().splitlines():
                parts = line.split()
                if len(parts) >= 5 and "LISTENING" in parts:
                    pid = int(parts[-1])
                    if pid > 0:
                        pids.add(pid)
        else:
            output = subprocess.check_output(f"lsof -ti:{port}", shell=True, text=True, stderr=subprocess.DEVNULL)
            for line in output.strip().splitlines():
                if line.isdigit():
                    pids.add(int(line))
    except Exception:
        pass
    return list(pids)

def kill_pid(pid: int) -> bool:
    try:
        if sys.platform == "win32":
            subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.kill(pid, signal.SIGTERM)
        return True
    except Exception:
        return False

def save_pid(pid: int):
    try:
        PID_FILE.write_text(str(pid))
    except Exception:
        pass

def get_saved_pid():
    try:
        if PID_FILE.exists():
            return int(PID_FILE.read_text().strip())
    except Exception:
        pass
    return None

def remove_pid():
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
    except Exception:
        pass

# =============================================================================
# CLI ENTRYPOINT
# =============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KrushiSetu Application Server Controller")
    parser.add_argument("action", nargs="?", default="start", choices=["start", "stop", "restart", "status"], help="Action to perform (default: start)")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host address to bind (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port number to bind (default: {DEFAULT_PORT})")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument("--daemon", "-d", action="store_true", help="Run server in background (daemon mode)")

    args = parser.parse_args()

    if args.action == "start":
        start_server(host=args.host, port=args.port, reload=not args.no_reload, daemon=args.daemon)
    elif args.action == "stop":
        stop_server(host=args.host, port=args.port)
    elif args.action == "restart":
        restart_server(host=args.host, port=args.port, reload=not args.no_reload)
    elif args.action == "status":
        show_status(host=args.host, port=args.port)
