# Maria Rozanova — Photography

A minimal, no-build photography portfolio: plain HTML/CSS/JS, hosted on GitHub Pages.

- **Repo:** https://github.com/mariarozzy/mariarozanova
- **Live site:** https://mariarozzy.github.io/mariarozanova/ (once Pages is turned on in repo Settings → Pages)

## Structure

- `index.html` — home page (banner, "Photography" heading, shuffled all-photos gallery)
- `nature.html`, `street.html`, `people.html` — the three galleries
- `about.html` — bio, philosophy, contact
- `projects.html` — marketing/graphic design case studies, **intentionally not linked from the nav**
- `style.css` — the whole design system (colors, type, layout) in one file
- `script.js` — the gear filter bar + home page shuffle
- `photos/<gallery>/<leica|iphone|film>/` — where your actual photos live
- `projects/<project-slug>/` — design files for each project on `projects.html`
- `build_galleries.py` — regenerates all the galleries above from whatever's in `photos/` and `projects/`

## Adding photos (no HTML editing needed)

**Option A — sort by hand:** drop image files into the matching folder, e.g. `photos/nature/leica/` for a nature shot taken on the Leica.
   - Folders: `nature`, `street`, `people` — each with `leica/`, `iphone/`, `film/` inside.

**Option B — the photo picker (easier when culling a lot of photos at once):**
1. Drop any number of candidate photos into `photos_inbox/` — mixed sizes and orientations are fine.
2. Run:
   ```
   python3 picker_server.py
   ```
   and open `http://localhost:8766/picker.html`.
3. Every photo in the inbox shows up as a thumbnail. Pick a gallery + gear for each and click **Assign** (moves it into the right `photos/` folder, GPS-stripped automatically), or **Discard** to set it aside — discarded photos move to `photos_inbox/_discarded/`, nothing is ever deleted, so it's safe to change your mind.
4. `photos_inbox/` is excluded from git, so nothing you haven't decided on can end up on the public site by accident.

Either way, once photos are sorted into `photos/`, run:
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
--sage: #7E9070;    /* labels, captions, nav */
--yellow: #F5DD90;  /* links, active states, the one accent */
--charcoal: #0D0F13;/* solid fills only */
```

Fonts (Playfair Display for headings, Inconsolata for labels/tags) load from Google Fonts at the top of `style.css`.
