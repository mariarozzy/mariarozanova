#!/usr/bin/env python3
"""
Rebuilds every photo grid on the site: the curated carousel and the
shuffled combined grid on index.html ("Gallery"), plus the per-project
galleries on projects.html — from whatever image files are sitting in
photos/<gallery>/<gear>/ and projects/<project>/. Nature/Urban/People
are just organizational folders (and photo-picker categories) now —
there's no separate page per gallery on the site itself.

Before building, it also strips GPS location data out of any photo that
still has it — this repo is public, so nothing here should leak where a
shot was taken. Requires: pip3 install --user Pillow pillow-heif

Usage:
    python3 build_galleries.py

Just drop photos into the matching folder (photos/nature/leica, etc., or
photos/featured/leica for the carousel, or projects/spanish-chamber/, etc.)
and rerun this. It only touches the blocks between GALLERY:START/END and
CAROUSEL:START/END comments — nothing else on the page is changed. The
combined "Gallery" grid on index.html shuffles client-side (script.js) on
every load; the carousel does not — it always shows photos/featured/ in
the order listed there.
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
GALLERIES = ["nature", "urban", "people"]
FEATURED = "featured"
GEAR_LABELS = {"leica": "Leica D-Lux 7", "iphone": "iPhone", "film": "Film"}
PROJECTS = ["spanish-chamber", "ama", "arch-sc", "design-theory"]
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


def find_project_images(project):
    folder = ROOT / "projects" / project
    if not folder.exists():
        return []
    return [f for f in sorted(folder.iterdir()) if f.suffix.lower() in IMAGE_EXTS]


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
            f'    <div class="tile" data-gear="{gear}" data-gallery="{gallery}">\n'
            f'      <img class="tile-img" src="{rel}" alt="">\n'
            f'      <div class="tile-cap">{label}</div>\n'
            f'    </div>'
        )
    return '  <div class="gallery-grid" id="homeGallery">\n' + '\n'.join(tiles) + '\n  </div>'


def render_carousel(photos):
    if not photos:
        return '  <div class="carousel-slide current"><div class="ph" style="position:absolute;inset:0;background:var(--charcoal);"></div></div>'
    slides = []
    for i, (_gear, path) in enumerate(photos):
        rel = path.relative_to(ROOT).as_posix()
        cls = "carousel-slide current" if i == 0 else "carousel-slide"
        slides.append(f'  <div class="{cls}"><img src="{rel}" alt=""></div>')
    return '\n'.join(slides)


def render_project_grid(project, images):
    if not images:
        return (
            '  <div class="gallery-grid">\n'
            '    <p style="color:var(--sage); font-family:var(--font-mono); '
            f'font-size:0.85rem;">No designs yet — drop files into projects/{project}/ '
            'and rerun build_galleries.py.</p>\n'
            '  </div>'
        )
    tiles = []
    for path in images:
        rel = path.relative_to(ROOT).as_posix()
        tiles.append(
            f'    <div class="tile">\n'
            f'      <img class="tile-img" src="{rel}" alt="">\n'
            f'    </div>'
        )
    return '  <div class="gallery-grid">\n' + '\n'.join(tiles) + '\n  </div>'


def update_page(page_name, grid_html_fn, marker="GALLERY", key=None):
    page = ROOT / page_name
    html = page.read_text()
    grid_html = grid_html_fn()

    start = re.escape(f"<!-- {marker}:START:{key}") if key else re.escape(f"<!-- {marker}:START")
    end = re.escape(f"<!-- {marker}:END:{key} -->") if key else re.escape(f"<!-- {marker}:END -->")
    pattern = re.compile(rf"({start}.*?-->\n).*?(\n\s*{end})", re.DOTALL)

    new_html, count = pattern.subn(lambda m: m.group(1) + grid_html + m.group(2), html)
    if count == 0:
        label = f"{page.name} [{marker}:{key}]" if key else f"{page.name} [{marker}]"
        print(f"  ! Couldn't find {marker}:START/END markers for {label} — skipped")
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

    # Nature/Urban/People are organizational folders only now — there's no
    # separate page per gallery on the site, just this one combined grid.
    # (The photo picker still uses these folders to sort photos into.)
    for gallery in GALLERIES:
        photos = find_photos(gallery)
        for _gear, path in photos:
            if strip_gps(path):
                stripped_count += 1
        all_photos.extend((gallery, gear, path) for gear, path in photos)
        print(f"  {gallery}/ — {len(photos)} photo(s)")

    update_page("index.html", lambda: render_home_grid(all_photos))
    print(f"  index.html [gallery] — {len(all_photos)} photo(s) (shuffled on each page load)")

    featured = find_photos(FEATURED)
    for _gear, path in featured:
        if strip_gps(path):
            stripped_count += 1
    update_page("index.html", lambda p=featured: render_carousel(p), marker="CAROUSEL")
    print(f"  index.html [carousel] — {len(featured)} featured photo(s)")

    for project in PROJECTS:
        images = find_project_images(project)
        for path in images:
            if strip_gps(path):
                stripped_count += 1
        update_page("projects.html", lambda i=images, p=project: render_project_grid(p, i), key=project)
        print(f"  projects.html [{project}] — {len(images)} design(s)")

    if stripped_count:
        print(f"  Removed GPS data from {stripped_count} file(s)")

    print("Done. Review the changes, then commit and push.")
