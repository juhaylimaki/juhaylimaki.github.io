# CLAUDE.md — Juha Ylimäki portfolio

## What this project is

Juha's games and visuals portfolio, moved off **Adobe Portfolio** (`juhaylimaki.myportfolio.com`) so he can cancel his Adobe subscription and keep the portfolio online for free.

- **Live site:** https://juhaylimaki.github.io
- **Repository:** https://github.com/juhaylimaki/juhaylimaki.github.io (public). GitHub Pages serves `main` from the repo root, and every push to `main` goes live in about a minute.
- **Old site:** https://juhaylimaki.myportfolio.com. It stays up until Adobe is cancelled and is the reference for content.

## ⚠️ Open work (in priority order)

1. **Upload the 20 videos to YouTube and link them.** This is the blocker before cancelling Adobe.
   - The old site plays every video through Adobe's player (`www-ccv.adobe.io`), and those players stop working when the subscription ends. Juha has the original video files.
   - On the new site every video currently shows a "Video coming soon" placeholder.
   - Per page: Casual Art 1, Indie Games at Muro Studios 5, Bugbear 1, Freelance Illustrations and Animations 10 (two of them side by side in a row), Aalto 3.
   - `docs/video-checklist.md` lists each video by page, position and caption.
   - Steps: Juha uploads each video (public or unlisted) and sends the links. Paste each link into that video's `"youtube_id"` in `content/site.json`; full URLs work. Run the build, the checker and the checklist (commands below), check locally, commit, and ask before pushing.
   - Each video block keeps its old `adobe_id`, which identifies which old video it was.
2. **LinkedIn link for the footer.** Juha hasn't given the URL yet. Set `contact.linkedin` in `site.json` to the full `https://www.linkedin.com/in/...` URL and rebuild.
3. **Cancel Adobe, only after #1 is done** and every video has been checked to play on the live site. Always remind Juha of this.
4. *(Optional, deferred from the code review)* Smaller improvements:
   - The lightbox loads the JPG/PNG rather than the WebP; a few PNGs are about 2.8 MB.
   - Rich-text fields aren't re-cleaned at build time.
   - A LinkedIn URL without `https://` gives a confusing checker error.
   - Home-tile alt text repeats the visible title, and the home page has no `<h1>`.
   - `tools/images.py` caches images by position, not by URL.
5. *(Optional)* A custom domain later, e.g. `juhaylimaki.com`: add a `CNAME` file and update `base_url` in `site.json`.

## How the site works

- **`content/site.json` is the single source of truth**: name, tagline, `base_url`, footer `about`, `contact` and the 5 projects. Each project has blocks of type `image`, `video`, `row` (side-by-side children) or `text`.
- `tools/build.py` renders the 6 pages (`index.html` plus one per project slug) from `site.json`. **The `*.html` files at the root are generated; never edit them by hand.** Change `site.json` and rebuild.
- Project slugs and their order (home-tile order): `casual-art`, `indie-stuff`, `bugbear-stuff`, `miscellaneous-stuff`, `aalto-university-stuff`. Previous/next links wrap around this order.
- `assets/css/style.css` holds all styling. Background is `#191919`, headings use Montserrat 700, body text uses Inter (Google Fonts).
- `assets/js/main.js` runs the lightbox (click an image; Esc, arrow keys, background is inert while open) and click-to-load YouTube (`youtube-nocookie.com`, delegated click handler). It has no dependencies.
- `assets/images/<slug>/`: `NN.jpg|png` plus `NN.webp`, max 2000px wide, and `cover.*` for the home tiles. Animated GIFs (`indie-stuff/34.gif`, `35.gif`) are copied unchanged.
- The site has no runtime dependencies. Python is only needed to rebuild the pages.

### Commands (Windows, run from the repo root)

```bash
python -m venv .venv                                         # one-time setup
.venv/Scripts/python -m pip install -r tools/requirements.txt
.venv/Scripts/python -m tools.build            # regenerate the HTML from site.json
.venv/Scripts/python -m tools.check_site       # must print "OK: 6 pages"
.venv/Scripts/python -m tools.video_checklist  # refresh docs/video-checklist.md
.venv/Scripts/python -m pytest tools/tests -q  # 44 tests, all must pass
.venv/Scripts/python -m http.server 8000       # local preview (also "site" in .claude/launch.json)
```

### Tools

| File | Purpose |
|---|---|
| `tools/scrape.py` | One-off: parsed the saved old pages (`tools/tests/fixtures/*.html`) into `site.json`. Don't re-run it; it would overwrite edits. |
| `tools/images.py` | One-off: downloaded the original images and made the web versions. `optimise()` is reusable for new images. |
| `tools/build.py` | Page builder. Errors name the project and block, and nothing is written if any page fails. |
| `tools/check_site.py` | Checks that every local file referenced exists, that images have alt text and dimensions, and that `.nojekyll` and `robots.txt` are present. |
| `tools/video_checklist.py` | Writes `docs/video-checklist.md`. It only ticks videos whose `youtube_id` is a valid YouTube link or ID. |

## Conventions and decisions

- **Ask Juha before every `git push`**, because a push publishes to the live site. Commit locally first.
- Work in TDD style: tests are in `tools/tests/`, and builder changes get a failing test first.
- All Python file I/O uses `encoding="utf-8"`, and the builder writes LF line endings. Windows defaults would garble "Ylimäki".
- **Footer email is deliberately shown as `juha.ylimaki(at)gmail.com` in plain text** (no mailto link), as protection against spam bots. The builder renders an email containing `@` as a mailto link and anything else as plain text.
- Footer About text: "Game Producer (with Game Artist, Animator, Level Designer, Game Designer experience)". It also feeds the home page meta description.
- `.nojekyll` stops GitHub from running Jekyll. `robots.txt` asks search engines to skip `/tools/`, `/docs/` and `/content/`; `tools/tests/fixtures/` holds copies of the old Adobe pages. These files are still publicly readable in the repo.
- Captions keep only `a`, `br`, `p`, `strong`/`b` and `em`/`i`. External links get `target="_blank" rel="noopener"`.
- The browser caches `main.js` and `style.css` hard during local preview. After changing them, refresh with `fetch(url, {cache: 'reload'})` or do a hard reload before verifying.

## Session history (2026-10-18)

1. **Design:** surveyed the old site (5 projects, 73 images, 20 Adobe-hosted videos, one side-by-side video row). Chose plain HTML/CSS on GitHub Pages with videos on YouTube, a faithful recreation plus light polish. Spec: `docs/superpowers/specs/2026-10-18-portfolio-recreation-design.md`. Plan: `docs/superpowers/plans/2026-10-18-portfolio-recreation.md`.
2. **Build, done inline task by task:**
   - scraped the content into `site.json`
   - downloaded the 78 original images (73 plus 5 covers) and optimised them to 37 MB
   - wrote the page builder, the stylesheet, the lightbox and the YouTube loader
   - added the site checker, the video checklist, the README and a favicon
3. **Final code review** by a separate reviewer found nothing critical. All important findings were fixed with tests: clear build errors, an honest video checklist, more YouTube link formats, lightbox focus handling, `.nojekyll` and `robots.txt`.
4. **Publishing:** Juha created the repo; it was first named `portfolio` and set to private, and was fixed to `juhaylimaki.github.io` and public. `build-site` was merged into `main` and pushed, and Pages switched on automatically. The live site was checked: all 163 referenced files load, the counts match the old site, and it works at phone width.
5. **Content tweaks after launch** (pushed): footer email changed to the `(at)` form, and the About text changed to the Game Producer line.

**Juha's preferences:** he works through the Claude desktop app and prefers plain-language steps for GitHub settings. He is fine with free hosting (no custom domain yet).
