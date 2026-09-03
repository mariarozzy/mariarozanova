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

from PIL import Image

from build_galleries import GEAR_LABELS, IMAGE_EXTS, GALLERIES, strip_gps

ROOT = Path(__file__).parent
INBOX = ROOT / "photos_inbox"
DISCARDED = INBOX / "_discarded"
CROP_POSITIONS_FILE = ROOT / "photos" / "crop-positions.json"
PORT = 8766


def load_crop_positions():
    """Per-photo focal point (as % of width/height) for how it's cropped in
    the gallery grid — read by build_galleries.py, written from the picker's
    'Adjust crop' tool. Photos with no entry just crop from the center."""
    if not CROP_POSITIONS_FILE.exists():
        return {}
    try:
        return json.loads(CROP_POSITIONS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_crop_positions(positions):
    CROP_POSITIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CROP_POSITIONS_FILE.write_text(json.dumps(positions, indent=2, sort_keys=True))


def resolve_under(base: Path, rel_path: str):
    """Resolve rel_path under base, refusing anything that escapes it."""
    if not rel_path:
        return None
    target = (base / rel_path).resolve()
    if base.resolve() not in target.parents:
        return None
    return target


def unique_dest(dest_dir: Path, name: str) -> Path:
    dest = dest_dir / name
    if not dest.exists():
        return dest
    stem, suffix, n = Path(name).stem, Path(name).suffix, 2
    while (dest_dir / f"{stem}-{n}{suffix}").exists():
        n += 1
    return dest_dir / f"{stem}-{n}{suffix}"


def guess_gear(rel_path: str) -> str:
    """Best-effort default gear guess from folder names, e.g. .../film/HK/x.jpg"""
    lower = rel_path.lower()
    if "film" in lower:
        return "film"
    if "leica" in lower:
        return "leica"
    return "iphone"


def list_inbox():
    INBOX.mkdir(exist_ok=True)
    files = []
    for f in INBOX.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in IMAGE_EXTS:
            continue
        if DISCARDED in f.parents:
            continue
        rel = f.relative_to(INBOX).as_posix()
        files.append({"path": rel, "guessedGear": guess_gear(rel)})
    return sorted(files, key=lambda x: x["path"])


def list_assigned():
    """Every photo already sorted into photos/<gallery>/<gear>/, so it can be
    reviewed and moved to a different gallery/gear without touching Finder."""
    positions = load_crop_positions()
    files = []
    for gallery in GALLERIES:
        for gear in GEAR_LABELS:
            folder = ROOT / "photos" / gallery / gear
            if not folder.exists():
                continue
            for f in sorted(folder.iterdir()):
                if f.is_file() and f.suffix.lower() in IMAGE_EXTS:
                    rel = f.relative_to(ROOT / "photos").as_posix()
                    pos = positions.get(rel, {})
                    files.append({
                        "path": rel,
                        "gallery": gallery,
                        "gear": gear,
                        "cropX": pos.get("x", 50),
                        "cropY": pos.get("y", 50),
                    })
    return files


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
        elif path == "/api/assigned":
            self._json({
                "files": list_assigned(),
                "galleries": GALLERIES,
                "gear": list(GEAR_LABELS.keys()),
                "gearLabels": GEAR_LABELS,
            })
        elif path.startswith("/inbox/"):
            self._file(INBOX / path[len("/inbox/"):])
        elif path.startswith("/photos/"):
            target = (ROOT / path.lstrip("/")).resolve()
            if (ROOT / "photos").resolve() not in target.parents:
                self.send_error(404)
                return
            self._file(target)
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

        if parsed.path == "/api/transform":
            self._handle_transform(payload)
        elif parsed.path == "/api/reassign":
            self._handle_reassign(payload)
        elif parsed.path == "/api/unassign":
            self._handle_unassign(payload)
        elif parsed.path == "/api/set-crop":
            self._handle_set_crop(payload)
        elif parsed.path in ("/api/assign", "/api/discard"):
            self._handle_inbox_action(parsed.path, payload)
        else:
            self.send_error(404)

    def _handle_inbox_action(self, route, payload):
        rel_path = payload.get("filename", "")  # may be a nested relative path
        src = (INBOX / rel_path).resolve() if rel_path else None
        # keep the move inside photos_inbox/, however deep — reject anything that escapes it
        if not rel_path or INBOX.resolve() not in src.parents:
            self._json({"error": "invalid path"}, 400)
            return
        if not src.exists():
            self._json({"error": "file not found"}, 404)
            return

        if route == "/api/assign":
            gallery = payload.get("gallery")
            gear = payload.get("gear")
            if gallery not in GALLERIES or gear not in GEAR_LABELS:
                self._json({"error": "invalid gallery/gear"}, 400)
                return
            dest_dir = ROOT / "photos" / gallery / gear
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = unique_dest(dest_dir, src.name)
            src.rename(dest)
            strip_gps(dest)
            self._json({"ok": True})
        else:  # /api/discard
            DISCARDED.mkdir(exist_ok=True)
            dest = unique_dest(DISCARDED, src.name)
            src.rename(dest)
            self._json({"ok": True})

    def _handle_reassign(self, payload):
        """Move a photo already sorted into photos/<gallery>/<gear>/ to a
        different gallery and/or gear."""
        rel_path = payload.get("path", "")
        gallery = payload.get("gallery")
        gear = payload.get("gear")
        src = resolve_under(ROOT / "photos", rel_path)
        if not src or gallery not in GALLERIES or gear not in GEAR_LABELS:
            self._json({"error": "invalid request"}, 400)
            return
        if not src.exists():
            self._json({"error": "file not found"}, 404)
            return

        dest_dir = ROOT / "photos" / gallery / gear
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = src if src.parent == dest_dir else unique_dest(dest_dir, src.name)
        if dest != src:
            src.rename(dest)
            # carry the saved crop position over to the new path, if any
            positions = load_crop_positions()
            if rel_path in positions:
                positions[dest.relative_to(ROOT / "photos").as_posix()] = positions.pop(rel_path)
                save_crop_positions(positions)
        self._json({"ok": True, "path": dest.relative_to(ROOT / "photos").as_posix()})

    def _handle_unassign(self, payload):
        """Pull a photo back out of the gallery into the discard pile —
        nothing is ever permanently deleted from here."""
        rel_path = payload.get("path", "")
        src = resolve_under(ROOT / "photos", rel_path)
        if not src:
            self._json({"error": "invalid request"}, 400)
            return
        if not src.exists():
            self._json({"error": "file not found"}, 404)
            return
        DISCARDED.mkdir(exist_ok=True)
        dest = unique_dest(DISCARDED, src.name)
        src.rename(dest)
        positions = load_crop_positions()
        if rel_path in positions:
            positions.pop(rel_path)
            save_crop_positions(positions)
        self._json({"ok": True})

    def _handle_set_crop(self, payload):
        """Save (or reset) the focal point used to crop this photo in the
        gallery grid — the file itself is never touched, just where the
        4:3 crop is centered when the site builds."""
        rel_path = payload.get("path", "")
        target = resolve_under(ROOT / "photos", rel_path)
        if not target or not target.exists():
            self._json({"error": "invalid request"}, 400)
            return

        positions = load_crop_positions()
        if payload.get("reset"):
            positions.pop(rel_path, None)
            save_crop_positions(positions)
            self._json({"ok": True, "x": 50, "y": 50})
            return

        try:
            x = max(0.0, min(100.0, float(payload.get("x"))))
            y = max(0.0, min(100.0, float(payload.get("y"))))
        except (TypeError, ValueError):
            self._json({"error": "invalid x/y"}, 400)
            return

        positions[rel_path] = {"x": round(x, 1), "y": round(y, 1)}
        save_crop_positions(positions)
        self._json({"ok": True, "x": positions[rel_path]["x"], "y": positions[rel_path]["y"]})

    def _handle_transform(self, payload):
        """Rotate, flip, or crop a photo in place — works on inbox photos and
        already-assigned ones alike, so a bad scan can be fixed on the spot."""
        source = payload.get("source")
        rel_path = payload.get("path", "")
        base = INBOX if source == "inbox" else (ROOT / "photos" if source == "photos" else None)
        target = resolve_under(base, rel_path) if base else None
        if not target:
            self._json({"error": "invalid request"}, 400)
            return
        if not target.exists():
            self._json({"error": "file not found"}, 404)
            return

        action = payload.get("action")
        try:
            with Image.open(target) as img:
                img.load()
                if action == "rotate":
                    degrees = str(payload.get("degrees"))
                    rotate_map = {"90": Image.ROTATE_90, "180": Image.ROTATE_180, "270": Image.ROTATE_270}
                    if degrees not in rotate_map:
                        self._json({"error": "invalid degrees"}, 400)
                        return
                    result = img.transpose(rotate_map[degrees])
                elif action == "flip":
                    axis = payload.get("axis")
                    flip_map = {"horizontal": Image.FLIP_LEFT_RIGHT, "vertical": Image.FLIP_TOP_BOTTOM}
                    if axis not in flip_map:
                        self._json({"error": "invalid axis"}, 400)
                        return
                    result = img.transpose(flip_map[axis])
                elif action == "crop":
                    box = payload.get("box")  # [x, y, w, h] in original-image pixels
                    if not (isinstance(box, list) and len(box) == 4):
                        self._json({"error": "invalid crop box"}, 400)
                        return
                    x, y, w, h = box
                    iw, ih = img.size
                    x = max(0, min(int(x), iw - 1))
                    y = max(0, min(int(y), ih - 1))
                    w = max(1, min(int(w), iw - x))
                    h = max(1, min(int(h), ih - y))
                    result = img.crop((x, y, x + w, y + h))
                else:
                    self._json({"error": "invalid action"}, 400)
                    return

                save_kwargs = {"quality": 95} if target.suffix.lower() in {".jpg", ".jpeg"} else {}
                result.save(target, **save_kwargs)
        except Exception as e:
            self._json({"error": f"couldn't process image: {e}"}, 500)
            return

        with Image.open(target) as img:
            w, h = img.size
        self._json({"ok": True, "width": w, "height": h})

    def log_message(self, fmt, *args):
        pass  # keep the terminal quiet


if __name__ == "__main__":
    INBOX.mkdir(exist_ok=True)
    print(f"Photo picker running at http://localhost:{PORT}/picker.html")
    print(f"Drop photos into {INBOX} and refresh the page to see them.")
    ThreadingHTTPServer(("localhost", PORT), Handler).serve_forever()
