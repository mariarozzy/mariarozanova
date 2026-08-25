#!/usr/bin/env python3
"""
Rebuilds the gallery grids in nature.html / street.html / people.html,
plus the combined all-photos grid on index.html, from whatever image
files are sitting in photos/<gallery>/<gear>/.

Before building, it also strips GPS location data out of any photo that
still has it — this repo is public, so nothing here should leak where a
shot was taken. Requires: pip3 install --user Pillow pillow-heif

Usage:
    python3 build_galleries.py

Just drop photos into the matching folder (photos/nature/leica, etc.)
and rerun this. It only touches the block between the GALLERY:START and
GALLERY:END comments in each page — nothing else on the page is changed.
The home page shuffles its grid client-side (script.js) on every load.
"""

import re
from pathlib import Path

try:
    from PIL import Image
    import pillow_heif
    pillow_heif.register_heif_opener()
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

ROOT = Path(__file__).parent
GALLERIES = ["nature", "street", "people"]
GEAR_LABELS = {"leica": "Leica D-Lux 7", "iphone": "iPhone", "film": "Film"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
GPS_IFD_TAG = 0x8825


def strip_gps(path):
    """Remove GPS EXIF data from a photo in place, if any is present.
    Leaves the file untouched if it's already clean, so reruns don't
    needlessly re-compress photos that were already processed."""
    if not HAS_PIL:
        return None
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            gps_ifd = exif.get_ifd(GPS_IFD_TAG)
            if not gps_ifd:
                return False
            save_kwargs = {}
            if path.suffix.lower() in {".jpg", ".jpeg", ".heic", ".webp"}:
                save_kwargs["quality"] = 95
            img.save(path, **save_kwargs)  # re-save with no exif= -> strips it
            return True
    except Exception as e:
        print(f"  ! Couldn't check/strip GPS data on {path.name}: {e}")
        return None


def find_photos(gallery):
    photos = []
    for gear in GEAR_LABELS:
        folder = ROOT / "photos" / gallery / gear
        if not folder.exists():
            continue
        for f in sorted(folder.iterdir()):
            if f.suffix.lower() in IMAGE_EXTS:
                photos.append((gear, f))
    return photos


def render_grid(photos):
    if not photos:
        return (
            '  <div class="gallery-grid">\n'
            '    <p style="color:var(--sage); font-family:var(--font-mono); '
            'font-size:0.85rem;">No photos yet — drop files into photos/&lt;gallery&gt;/'
            '&lt;leica|iphone|film&gt;/ and rerun build_galleries.py.</p>\n'
            '  </div>'
        )
    tiles = []
    for gear, path in photos:
        rel = path.relative_to(ROOT).as_posix()
        label = GEAR_LABELS[gear]
        tiles.append(
            f'    <div class="tile" data-gear="{gear}">\n'
            f'      <img class="tile-img" src="{rel}" alt="">\n'
            f'      <div class="tile-cap">{label}</div>\n'
            f'    </div>'
        )
    return '  <div class="gallery-grid">\n' + '\n'.join(tiles) + '\n  </div>'


def render_home_grid(all_photos):
    if not all_photos:
        return (
            '  <div class="gallery-grid" id="homeGallery">\n'
            '    <p style="color:var(--sage); font-family:var(--font-mono); '
            'font-size:0.85rem;">No photos yet — drop files into photos/&lt;gallery&gt;/'
            '&lt;leica|iphone|film&gt;/ and rerun build_galleries.py.</p>\n'
            '  </div>'
        )
    tiles = []
    for gallery, gear, path in all_photos:
        rel = path.relative_to(ROOT).as_posix()
        label = GEAR_LABELS[gear]
        tiles.append(
            f'    <a class="tile" data-gear="{gear}" href="{gallery}.html">\n'
            f'      <img class="tile-img" src="{rel}" alt="">\n'
            f'      <div class="tile-cap">{label}</div>\n'
            f'    </a>'
        )
    return '  <div class="gallery-grid" id="homeGallery">\n' + '\n'.join(tiles) + '\n  </div>'


def update_page(gallery, grid_html_fn, marker_file=None):
    page = ROOT / (marker_file or f"{gallery}.html")
    html = page.read_text()
    grid_html = grid_html_fn()

    pattern = re.compile(
        r"(<!-- GALLERY:START.*?-->\n).*?(\n\s*<!-- GALLERY:END -->)",
        re.DOTALL,
    )
    new_html, count = pattern.subn(lambda m: m.group(1) + grid_html + m.group(2), html)
    if count == 0:
        print(f"  ! Couldn't find GALLERY:START/END markers in {page.name} — skipped")
        return
    page.write_text(new_html)


if __name__ == "__main__":
    if not HAS_PIL:
        print("! Pillow not installed — GPS data in photos won't be checked/stripped.")
        print("  Run: pip3 install --user Pillow pillow-heif")
        print()

    print("Rebuilding galleries...")
    all_photos = []
    stripped_count = 0
    for gallery in GALLERIES:
        photos = find_photos(gallery)
        for _gear, path in photos:
            if strip_gps(path):
                stripped_count += 1
        all_photos.extend((gallery, gear, path) for gear, path in photos)
        update_page(gallery, lambda p=photos: render_grid(p))
        print(f"  {gallery}.html — {len(photos)} photo(s)")

    if stripped_count:
        print(f"  Removed GPS data from {stripped_count} photo(s)")

    update_page(None, lambda: render_home_grid(all_photos), marker_file="index.html")
    print(f"  index.html — {len(all_photos)} photo(s) (shuffled on each page load)")
    print("Done. Review the changes, then commit and push.")
