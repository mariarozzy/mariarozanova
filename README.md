# Your Name — Photography

A minimal, no-build photography portfolio: plain HTML/CSS/JS, ready for GitHub Pages.

## Structure

- `index.html` — home page (hero + thesis line)
- `nature.html`, `street.html`, `people.html` — the three galleries, one shared template
- `about.html` — bio, philosophy, availability
- `work.html` — marketing/graphic design, **intentionally not linked from the nav**
- `style.css` — the whole design system (colors, type, layout) in one file
- `script.js` — the gear filter bar on gallery pages
- `assets/images/` — drop your photos here

## Publish it on GitHub Pages

1. Create a new repository on GitHub (public, no README/gitignore needed — this folder already has them).
2. From this folder, run:
   ```
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
   git branch -M main
   git push -u origin main
   ```
3. On GitHub: **Settings → Pages → Source → Deploy from a branch → main / (root)**.
4. Your site is live at `https://YOUR-USERNAME.github.io/YOUR-REPO/` a minute or two later.

To use a custom domain, add a `CNAME` file with your domain in it, and point your domain's DNS at GitHub Pages per [their docs](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site).

## Adding photos

Each gallery page has placeholder tiles like this:

```html
<div class="tile" data-gear="leica">
  <div class="tile-img"></div>
  <div class="tile-cap">Leica D-Lux 7</div>
</div>
```

To swap in a real photo:
1. Put the image file in `assets/images/`.
2. Replace `<div class="tile-img"></div>` with `<img class="tile-img" src="assets/images/your-file.jpg" alt="">`.
3. Set `data-gear` to `leica`, `iphone`, or `film` so the filter bar picks it up.
4. Copy/paste the whole `<div class="tile">...</div>` block to add more — delete extras to remove.

Same pattern for the hero image on `index.html` (the empty `.hero-image` div near the top).

## Keeping "Work" unlisted

`work.html` exists and works, but nothing on the site links to it and it's marked `noindex` — visit it directly at `yoursite.com/work.html`, or send that link when you want to share it. When you're ready to make it public, add `<a href="work.html">Work</a>` to the nav in each page's `<div class="site-nav-links">`.

## Editing the palette or type

Everything is CSS custom properties at the top of `style.css`:

```css
--bg: #16233A;      /* navy background */
--ink: #F7F5EE;     /* body text + headings */
--sage: #7E9070;    /* labels, captions, nav */
--yellow: #F5DD90;  /* links, active states, the one accent */
--charcoal: #0D0F13;/* solid fills only */
```

Fonts (Playfair Display for headings, Inconsolata for labels/tags) load from Google Fonts at the top of `style.css` — no local files to manage.
