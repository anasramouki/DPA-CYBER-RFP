"""
CyberRFP Maroc - Standalone Windows Desktop Launcher
Runs the local procurement monitoring server and automatically opens the browser.
"""
import os
import sys
import time
import socket
import webbrowser
import threading

# Reconfigure console output encoding to utf-8 safely on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import uvicorn

# Ensure package directory is importable
if getattr(sys, "frozen", False):
    APP_DIR = sys._MEIPASS
    sys.path.insert(0, APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, APP_DIR)

from src.server import app


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def get_available_port(default_port: int = 8000) -> int:
    port = default_port
    while is_port_in_use(port):
        port += 1
    return port


def get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def open_browser_after_delay(url: str, delay_seconds: float = 1.2):
    time.sleep(delay_seconds)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main():
    port = get_available_port(8000)
    lan_ip = get_lan_ip()
    local_url = f"http://127.0.0.1:{port}"
    mobile_url = f"http://{lan_ip}:{port}"

    os.environ["CYBERRFP_PORT"] = str(port)
    os.environ["CYBERRFP_LAN_IP"] = lan_ip

    print("=" * 72)
    print("  [*] CYBERRFP MAROC — DATA PROTECH COMPANY (DPA)")
    print("      VEILLE MARCHES PUBLICS CYBERSECURITE & ALERTES TEMPS REEL")
    print("=" * 72)
    print(f"  [>] Acces Local (PC / Laptop) : {local_url}")
    print(f"  [>] Acces iPhone / Mobile LAN : {mobile_url}")
    print("  [>] Authentification          : Comptes officiels @dpg-cyber.com ou HTTP Basic")
    admin_pw = os.environ.get("ADMIN_PASSWORD", "cyberrfp2026")
    if admin_pw == "cyberrfp2026":
        print("  [!] SECURITE : Mot de passe admin par defaut (cyberrfp2026).")
        print("      Modifiez ADMIN_PASSWORD dans .env pour les environnements de production.")
    print("  [>] Base de Donnees SQLite    : cyberrfp.db (Synchronisation live)")
    print("  [>] Support iOS / PWA         : Compatible Safari iPhone & Notifications")
    print("=" * 72)
    print("  Ouverture automatique du tableau de bord...")
    print("  (Pour arreter le serveur, fermez cette fenetre ou appuyez sur Ctrl+C)")
    print("=" * 72 + "\n")

    # Launch browser opener in background thread
    threading.Thread(target=open_browser_after_delay, args=(local_url,), daemon=True).start()

    # Start Uvicorn ASGI server bound to 0.0.0.0 for LAN & iPhone access
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
