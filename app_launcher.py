import sys
import os
import argparse
import webbrowser
import threading
import time

def run_qt_gui():
    try:
        from app_gui_qt import main as qt_main
        print("[Launcher] Starting PyQt6 Native Desktop GUI...")
        qt_main()
    except Exception as e:
        print(f"[Launcher] Could not launch Qt GUI ({e}). Falling back to Web/Desktop Browser interface...")
        run_web_gui(auto_open=True)

def run_web_gui(host="0.0.0.0", port=8000, auto_open=True):
    import uvicorn
    from app_server import app

    def open_browser():
        time.sleep(1.2)
        url = f"http://localhost:{port}"
        print(f"[Launcher] Opening {url} in browser...")
        try:
            webbrowser.open(url)
        except Exception:
            pass

    if auto_open and host != "0.0.0.0":
        threading.Thread(target=open_browser, daemon=True).start()

    print(f"[Launcher] Starting Server on http://{host}:{port}...")
    uvicorn.run(app, host=host, port=port, log_level="info")

def main():
    parser = argparse.ArgumentParser(description="NSFW Image Hunter & Downloader")
    parser.add_argument("--mode", choices=["gui", "web", "server"], default="web",
                        help="Run mode: 'gui' (PyQt6 native window), 'web' (Browser window), 'server' (API server only)")
    parser.add_argument("--port", type=int, default=8000, help="Port for web server (default: 8000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    args = parser.parse_args()

    if args.mode == "gui":
        run_qt_gui()
    elif args.mode == "server":
        run_web_gui(host=args.host, port=args.port, auto_open=False)
    else:
        run_web_gui(host=args.host, port=args.port, auto_open=False)

if __name__ == "__main__":
    main()
