#!/usr/bin/env python3
"""Python 3.10+: run the complete local VAN DAO browser game, with no packages to install."""

from __future__ import annotations

import argparse
import errno
import logging
from pathlib import Path
import sys
import threading
import webbrowser


def main(argv=None):
    if sys.version_info < (3, 10):
        print("VAN DAO needs Python 3.10 or newer. Install Python, then run: python run.py", file=sys.stderr)
        return 1
    parser = argparse.ArgumentParser(description="Start VAN DAO: IMMORTAL WAR in your local browser.")
    parser.add_argument("--host", default="127.0.0.1", help="Server bind address (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="Preferred local port (default: 8000; occupied ports are skipped).")
    parser.add_argument("--no-browser", action="store_true", help="Start the server without opening a browser tab.")
    parser.add_argument("--verbose", action="store_true", help="Log individual local HTTP requests.")
    args = parser.parse_args(argv)
    if not 0 <= args.port <= 65_535:
        parser.error("--port must be between 0 and 65535.")
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING, format="%(levelname)s: %(message)s")
    web_root = Path(__file__).resolve().parent / "web"
    if not (web_root / "index.html").is_file():
        print("Game files are incomplete. Extract the entire GitHub ZIP, then run run.py from that folder.", file=sys.stderr)
        return 1
    from game.server import create_server

    server = None
    candidates = [0] if args.port == 0 else range(args.port, min(args.port + 21, 65_536))
    try:
        for port in candidates:
            try:
                server = create_server(args.host, port, web_root)
                break
            except OSError as error:
                if error.errno not in (errno.EADDRINUSE, 10048):
                    raise
        if server is None:
            print("No available local port was found. Try: python run.py --port 9000", file=sys.stderr)
            return 1
        port = server.server_address[1]
        browser_host = "127.0.0.1" if args.host == "0.0.0.0" else args.host
        address = f"http://{browser_host}:{port}/"
        print("\nVAN DAO: IMMORTAL WAR", flush=True)
        print(f"Local game: {address}", flush=True)
        print("Keep this terminal open while playing. Press Ctrl+C to stop.\n", flush=True)
        if not args.no_browser:
            def open_game():
                try:
                    if not webbrowser.open(address):
                        print("Open the local game address above in your browser.", flush=True)
                except webbrowser.Error:
                    print("Open the local game address above in your browser.", flush=True)
            opener = threading.Timer(0.4, open_game)
            opener.daemon = True
            opener.start()
        server.serve_forever(poll_interval=0.1)
    except KeyboardInterrupt:
        print("\nLocal game stopped.", flush=True)
    except OSError as error:
        print(f"Could not start the local game: {error}", file=sys.stderr)
        return 1
    finally:
        if server is not None:
            server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
