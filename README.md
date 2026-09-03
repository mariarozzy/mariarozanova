# Maria Rozanova — Photography

A minimal, no-build photography portfolio: plain HTML/CSS/JS, hosted on GitHub Pages.

- **Repo:** https://github.com/mariarozzy/mariarozanova
- **Live site:** https://mariarozzy.github.io/mariarozanova/ (once Pages is turned on in repo Settings → Pages)

## Structure

`index.html` is the whole photo side of the site — one scrolling page with the nav jumping straight to each section instead of loading a separate page:

- Carousel — curated, not random. Only shows what's in `photos/featured/`.
- `#all` — every photo across every gallery, shuffled into a new order each page load.
- `#nature`, `#urban`, `#people` — the three galleries, each with its own gear filter chips.

Other pages:
- `about.html` — bio, philosophy, contact, portrait
- `projects.html` — marketing/graphic design case studies, **intentionally not linked from the nav**
- `style.css` — the whole design system (colors, type, layout) in one file
- `script.js` — filter chips, the "All" shuffle, the carousel auto-advance, the click-to-expand lightbox
- `photos/<gallery>/<leica|iphone|film>/` — where your actual photos live (`nature`, `urban`, `people`, plus `featured` for the carousel)
- `projects/<project-slug>/` — design files for each project on `projects.html`
- `build_galleries.py` — regenerates every section above from whatever's in `photos/` and `projects/`

## Adding photos (no HTML editing needed)

**Option A — sort by hand:** drop image files into the matching folder, e.g. `photos/nature/leica/` for a nature shot taken on the Leica.
   - Folders: `nature`, `urban`, `people` — each with `leica/`, `iphone/`, `film/` inside.
   - For the carousel: `photos/featured/<leica|iphone|film>/` — just your best shots, shown in the order they sit in the folder (not shuffled).

**Option B — the photo picker (easier when culling a lot of photos at once):**
1. Drop any number of candidate photos into `photos_inbox/` — mixed sizes and orientations are fine.
2. Run:
   ```
   python3 picker_server.py
   ```
   and open `http://localhost:8766/picker.html`.
3. **Inbox** section: every photo in the inbox shows up as a thumbnail. Pick a gallery + gear for each and click **Assign** (moves it into the right `photos/` folder, GPS-stripped automatically), or **Discard** to set it aside — discarded photos move to `photos_inbox/_discarded/`, nothing is ever deleted, so it's safe to change your mind.
4. **Already in the gallery** section: every photo already sorted into `photos/`, so you can catch one that landed in the wrong gallery — change its gallery/gear dropdowns and click **Move**, or **Remove** to pull it back out.
5. Click any thumbnail (in either section) to rotate, flip, or crop it right there — useful since some film scans don't carry orientation data, so a sideways shot won't fix itself automatically.
6. `photos_inbox/` is excluded from git, so nothing you haven't decided on can end up on the public site by accident.

Either way, once photos are sorted into `photos/`, run:
   ```
   python3 build_galleries.py
   ```
   This rewrites the carousel and every gallery section on `index.html` to include every photo currently sitting in its folder — nothing else on the page is touched. It also strips any GPS location data out of the photo files themselves before building, since this repo is public (needs `pip3 install --user Pillow pillow-heif` once, if not already installed).
3. Commit and push:
   ```
   git add -A
   git commit -m "Add photos"
   git push
   ```

To remove a photo, delete the file from its `photos/` subfolder and rerun the script. Order on the page follows filename order within each gear folder — rename files with a number prefix (`01-`, `02-`...) if you want to control the sequence (this is what decides carousel order too, since that one isn't shuffled).

If you'd rather not touch the terminal at all, just tell Claude "I added photos to [folder]" and it'll run the script and push for you.

## Adding project designs (projects.html)

Same idea as photos, one folder per project:

- `projects/spanish-chamber/`
- `projects/ama/`
- `projects/arch-sc/`
- `projects/design-theory/`

Drop design files into the matching folder and run `python3 build_galleries.py` — it fills in that project's gallery on `projects.html` without touching the title, date, or description text. Edit those directly in `projects.html` (each is a plain `<h2>`, `<span class="project-date">`, and `<p class="project-desc">`).

To add a whole new project: copy one `<section class="project">...</section>` block in `projects.html`, give its gallery markers a new unique key (e.g. `GALLERY:START:my-new-project` / `GALLERY:END:my-new-project`), add the matching slug to the `PROJECTS` list at the top of `build_galleries.py`, and create `projects/my-new-project/`.

## Editing anything else

Simplest: tell Claude what to change in this chat. It edits the files and pushes.

## Keeping "Projects" unlisted

`projects.html` exists and works, but nothing on the site links to it and it's marked `noindex` — visit it directly at `/projects.html`, or share that link directly. To make it public, add `<a href="projects.html">Projects</a>` to the nav (`.site-nav-links`) in each page.

## Editing the palette or type

Everything is CSS custom properties at the top of `style.css`:

```css
--bg: #16233A;      /* navy background */
--ink: #F7F5EE;     /* body text + headings */
--sage: #8FA3C9;    /* labels, captions, nav */
--pink: #E88CA8;    /* hover accent on gallery tiles / about-page blob */
--green: #8FBF6E;   /* hover accent on gallery tiles / about-page blob */
--yellow: #F5DD90;  /* links, active nav state, filter chips */
--charcoal: #0D0F13;/* solid fills only */
```

Fonts load from Google Fonts at the top of `style.css`: Space Grotesk for headings, Caveat (the script) for the "Maria Rozanova" nav mark, Literata for body text, Inconsolata for labels/tags/nav links.
