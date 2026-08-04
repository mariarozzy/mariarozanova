#!/usr/bin/env python3
"""
Rebuilds the gallery grids in nature.html / street.html / people.html
from whatever image files are sitting in photos/<gallery>/<gear>/.

Usage:
    python3 build_galleries.py

Just drop photos into the matching folder (photos/nature/leica, etc.)
and rerun this. It only touches the block between the GALLERY:START and
GALLERY:END comments in each page — nothing else on the page is changed.
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent
GALLERIES = ["nature", "street", "people"]
GEAR_LABELS = {"leica": "Leica D-Lux 7", "iphone": "iPhone", "film": "Film"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}


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


def update_page(gallery):
    page = ROOT / f"{gallery}.html"
    html = page.read_text()
    photos = find_photos(gallery)
    grid_html = render_grid(photos)

    pattern = re.compile(
        r"(<!-- GALLERY:START.*?-->\n).*?(\n\s*<!-- GALLERY:END -->)",
        re.DOTALL,
    )
    new_html, count = pattern.subn(lambda m: m.group(1) + grid_html + m.group(2), html)
    if count == 0:
        print(f"  ! Couldn't find GALLERY:START/END markers in {page.name} — skipped")
        return
    page.write_text(new_html)
    print(f"  {gallery}.html — {len(photos)} photo(s)")


if __name__ == "__main__":
    print("Rebuilding galleries...")
    for gallery in GALLERIES:
        update_page(gallery)
    print("Done. Review the changes, then commit and push.")
