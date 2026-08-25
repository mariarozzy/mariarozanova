# Maria Rozanova — Photography

A minimal, no-build photography portfolio: plain HTML/CSS/JS, hosted on GitHub Pages.

- **Repo:** https://github.com/mariarozzy/mariarozanova
- **Live site:** https://mariarozzy.github.io/mariarozanova/ (once Pages is turned on in repo Settings → Pages)

## Structure

- `index.html` — home page (hero + thesis line)
- `nature.html`, `street.html`, `people.html` — the three galleries
- `about.html` — bio, philosophy, contact
- `work.html` — marketing/graphic design, **intentionally not linked from the nav**
- `style.css` — the whole design system (colors, type, layout) in one file
- `script.js` — the gear filter bar on gallery pages
- `photos/<gallery>/<leica|iphone|film>/` — where your actual photos live
- `build_galleries.py` — regenerates the gallery pages from whatever's in `photos/`

## Adding photos (no HTML editing needed)

1. Drop image files into the matching folder, e.g. `photos/nature/leica/` for a nature shot taken on the Leica.
   - Folders: `nature`, `street`, `people` — each with `leica/`, `iphone/`, `film/` inside.
2. Run:
   ```
   python3 build_galleries.py
   ```
   This rewrites the gallery grid on the matching page (`nature.html`, `street.html`, or `people.html`) to include every photo currently sitting in its folders — nothing else on the page is touched. It also strips any GPS location data out of the photo files themselves before building, since this repo is public (needs `pip3 install --user Pillow pillow-heif` once, if not already installed).
3. Commit and push:
   ```
   git add -A
   git commit -m "Add photos"
   git push
   ```

To remove a photo, delete the file from its `photos/` subfolder and rerun the script. Order on the page follows filename order within each gear folder — rename files with a number prefix (`01-`, `02-`...) if you want to control the sequence.

If you'd rather not touch the terminal at all, just tell Claude "I added photos to [folder]" and it'll run the script and push for you.

## Editing anything else

Simplest: tell Claude what to change in this chat. It edits the files and pushes.

## Keeping "Work" unlisted

`work.html` exists and works, but nothing on the site links to it and it's marked `noindex` — visit it directly at `/work.html`, or share that link directly. To make it public, add `<a href="work.html">Work</a>` to the nav (`.site-nav-links`) in each page.

## Editing the palette or type

Everything is CSS custom properties at the top of `style.css`:

```css
--bg: #16233A;      /* navy background */
--ink: #F7F5EE;     /* body text + headings */
--sage: #7E9070;    /* labels, captions, nav */
--yellow: #F5DD90;  /* links, active states, the one accent */
--charcoal: #0D0F13;/* solid fills only */
```

Fonts (Playfair Display for headings, Inconsolata for labels/tags) load from Google Fonts at the top of `style.css`.
