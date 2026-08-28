#!/usr/bin/env python3
"""
A tiny local tool for sorting photos into the site's gallery folders by hand,
from a browser, instead of moving files around in Finder.

Usage:
    python3 picker_server.py
    then open http://localhost:8766/picker.html

Workflow:
    1. Drop any number of candidate photos into photos_inbox/
    2. Open the picker page — every photo in the inbox shows up as a thumbnail
    3. For each one: pick a gallery (Nature/Street/People) + gear (Leica/iPhone/Film)
       and click Assign, or click Discard to set it aside
    4. Assigned photos move into photos/<gallery>/<gear>/ (GPS-stripped on the way,
       same as build_galleries.py does)
    5. Discarded photos move into photos_inbox/_discarded/ — nothing is deleted,
       so it's safe to change your mind later
    6. Run `python3 build_galleries.py` afterward to rebuild the site pages
"""

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from build_galleries import GEAR_LABELS, IMAGE_EXTS, GALLERIES, strip_gps

ROOT = Path(__file__).parent
INBOX = ROOT / "photos_inbox"
DISCARDED = INBOX / "_discarded"
PORT = 8766


def list_inbox():
    INBOX.mkdir(exist_ok=True)
    return sorted(
        f.name for f in INBOX.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTS
    )


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path):
        if not path.exists() or not path.is_file():
            self.send_error(404)
            return
        ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/" or path == "/picker.html":
            self._file(ROOT / "picker.html")
        elif path == "/api/inbox":
            self._json({
                "files": list_inbox(),
                "galleries": GALLERIES,
                "gear": list(GEAR_LABELS.keys()),
                "gearLabels": GEAR_LABELS,
            })
        elif path.startswith("/inbox/"):
            self._file(INBOX / path[len("/inbox/"):])
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._json({"error": "bad request body"}, 400)
            return

        filename = payload.get("filename", "")
        src = (INBOX / filename)
        # keep the move inside photos_inbox/ — reject anything that isn't a plain filename
        if not filename or src.parent.resolve() != INBOX.resolve():
            self._json({"error": "invalid filename"}, 400)
            return
        if not src.exists():
            self._json({"error": "file not found"}, 404)
            return

        if parsed.path == "/api/assign":
            gallery = payload.get("gallery")
            gear = payload.get("gear")
            if gallery not in GALLERIES or gear not in GEAR_LABELS:
                self._json({"error": "invalid gallery/gear"}, 400)
                return
            dest_dir = ROOT / "photos" / gallery / gear
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / src.name
            src.rename(dest)
            strip_gps(dest)
            self._json({"ok": True})

        elif parsed.path == "/api/discard":
            DISCARDED.mkdir(exist_ok=True)
            src.rename(DISCARDED / src.name)
            self._json({"ok": True})

        else:
            self.send_error(404)

    def log_message(self, fmt, *args):
        pass  # keep the terminal quiet


if __name__ == "__main__":
    INBOX.mkdir(exist_ok=True)
    print(f"Photo picker running at http://localhost:{PORT}/picker.html")
    print(f"Drop photos into {INBOX} and refresh the page to see them.")
    ThreadingHTTPServer(("localhost", PORT), Handler).serve_forever()
