# Portfolio Recreation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move Juha's Adobe Portfolio site to a self-owned static site on GitHub Pages, with the same content and light polish, so the Adobe subscription can be cancelled.

**Architecture:** A one-off Python scraper turns the current site into `content/site.json` and downloads the original images. A Python image step writes web-sized images into `assets/images/`. A Python builder renders 6 static HTML pages from `site.json`, which are committed and served as-is by GitHub Pages. One CSS file and one small vanilla JS file (lightbox and click-to-load YouTube) cover presentation and behaviour.

**Tech Stack:** HTML5, CSS, vanilla JS (no build). Python 3.14 tools in a `.venv`: `requests`, `beautifulsoup4`, `Pillow`, `pytest`. Google Fonts Montserrat and Inter.

**Spec:** `docs/superpowers/specs/2026-10-18-portfolio-recreation-design.md`

## Global Constraints

- The live site has no runtime dependencies other than Google Fonts and YouTube embeds. No npm and no frameworks.
- All Python file I/O passes `encoding="utf-8"` explicitly, because Windows defaults to cp1252 and the name is "Ylimäki".
- Every HTML page has `<meta charset="utf-8">`, `<html lang="en">`, a `<title>`, a meta description and Open Graph title/description/image.
- Page slugs: `casual-art`, `indie-stuff`, `bugbear-stuff`, `miscellaneous-stuff`, `aalto-university-stuff`, in this order (home-tile order). Files are `<slug>.html` plus `index.html`.
- Header text: "JUHA YLIMÄKI" (links to `index.html`) and "GAMES AND VISUALS". Page background `#191919`.
- Images: max 2000px wide, WebP quality 82 plus a fallback (JPEG quality 85, or PNG if the source is PNG). Animated GIFs are copied unchanged.
- Image file names: `assets/images/<slug>/NN.<ext>` (two digits, in document order, including images inside rows) and `assets/images/<slug>/cover.<ext>`.
- YouTube embeds use `https://www.youtube-nocookie.com/embed/<id>`.
- External links open with `target="_blank" rel="noopener"`.
- `base_url` is `https://juhaylimaki.github.io`.
- Run Python as `.venv/Scripts/python` from the repo root (Windows venv layout).

## Review Focus

1. **Captions are duplicated in the source HTML.** Each caption container holds the `.module-caption` element twice (164 elements for 82 containers). The scraper must take only the first, or every caption appears twice. *(Task 1 test `test_captions_not_duplicated`)*
2. **Pasted YouTube URLs come in many shapes,** such as `watch?v=ID&t=30s`, `youtu.be/ID?si=…` and `shorts/ID`. Each must resolve to the bare 11-character ID; garbage must raise, not render a broken embed. *(Task 3 test `test_youtube_id_forms`)*
3. **Non-ASCII text** ("Ylimäki", curly quotes, "–") must survive scrape → JSON → HTML on Windows. *(Task 1 `test_unicode_roundtrip`, Task 3 `test_build_writes_utf8`)*
4. **An interrupted download** (network drop partway through 73 images) must not leave a truncated file that a re-run then trusts. *(Task 2 `test_download_atomic_and_skips_existing`)*
5. **Images with no caption** must still get meaningful alt text and no empty `<figcaption>`. *(Task 3 `test_image_without_caption`)*

---

### Task 1: Python tooling and scraper → `content/site.json`

**Files:**
- Create: `tools/requirements.txt`, `tools/__init__.py`, `tools/scrape.py`, `tools/tests/__init__.py`, `tools/tests/test_scrape.py`, `tools/tests/fixtures/{work,casual-art,indie-stuff,bugbear-stuff,miscellaneous-stuff,aalto-university-stuff}.html`, `content/site.json`
- Modify: `.gitignore` (add `.venv/`, `__pycache__/`, `.pytest_cache/`)

**Interfaces:**
- Produces the `site.json` schema that every later task uses:
  ```
  Site    = {name: "Juha Ylimäki", tagline: "Games and Visuals", base_url: str,
             about: str, contact: {email: str, linkedin: str}, projects: [Project]}
  Project = {slug, title, description_html, cover: Image, blocks: [Block]}
  Block   = Image | Video | Text | Row
  Image   = {type:"image", source_url, caption_html, file:null, ext:null, width:null, height:null, webp:null}
  Video   = {type:"video", adobe_id, youtube_id:"", caption_html}
  Text    = {type:"text", html}
  Row     = {type:"row", children:[Block]}
  ```
  `about` starts as `"Game artist, animator, level designer and game designer."`, and `contact` starts with empty strings (filled in Task 6).
- `clean_rich_text(html: str) -> str`: keeps `a[href]` (http/https/mailto only, plus `target="_blank" rel="noopener"` on http/https), `br`, `p`, `strong`, `b`, `em`, `i`; unwraps every other tag to its text; drops `script`/`style` with their contents; trims whitespace.
- `parse_project(html: str, slug: str) -> dict`: returns a Project. Title from `.page-header .title`, description from `.page-header .description`. Blocks come from the top-level `.project-module` elements inside `main`, in order: `project-module-image` → Image with `source_url` = the `.js-lightbox` `data-src` (original file); `project-module-video` → Video with `adobe_id` taken from the iframe `src` path `/ccv/<id>/embed`; `project-module-tree` → Row of its child modules; `project-module-text` → Text. Any other module type raises `ValueError(f"unknown module {cls} on {slug}")`. The caption is the first `.module-caption` in the module, cleaned.
- `parse_home(html: str) -> list[dict]`: returns `[{slug, title, cover_url}]` from `main a.project-cover`, in order. `cover_url` is the `img` `data-src`, else `src` when it starts with `http`.
- `main()` reads the fixtures, builds the Site and writes `content/site.json` (indent 2, `ensure_ascii=False`).

- [ ] **Step 1: Set up the venv and save fixtures**

```bash
python -m venv .venv
.venv/Scripts/python -m pip install requests==2.32.3 beautifulsoup4==4.12.3 Pillow==11.3.0 pytest==8.3.4
.venv/Scripts/python -m pip freeze > tools/requirements.txt
for p in work casual-art indie-stuff bugbear-stuff miscellaneous-stuff aalto-university-stuff; do curl -sSfL "https://juhaylimaki.myportfolio.com/$p" -o "tools/tests/fixtures/$p.html"; done
```
Expected: 6 non-empty fixture files. If a pinned version doesn't install on Python 3.14, use the nearest newer release and record it in `requirements.txt`.

- [ ] **Step 2: Write failing tests** in `tools/tests/test_scrape.py` (fixtures loaded with `encoding="utf-8"`):
  - `test_home_tiles`: `[t["slug"] for t in parse_home(work)] == ["casual-art","indie-stuff","bugbear-stuff","miscellaneous-stuff","aalto-university-stuff"]`, and every `cover_url` starts with `https://cdn.myportfolio.com/`.
  - `test_bugbear_blocks`: the title equals `"AAA Level Designer at Bugbear Entertainment"`; block types are `["video","image","image","image","image","image"]`; `blocks[0]["adobe_id"] == "SgRdi4Y5_Cc"`; the description starts with `"Worked as a Level Designer"`.
  - `test_totals`: across all 5 projects, counting images and videos inside rows too: 73 images and 20 videos.
  - `test_misc_row`: `miscellaneous-stuff` has exactly one Row with at least 2 children, all videos.
  - `test_original_image_url`: no Image `source_url` contains `_rw_`.
  - `test_captions_not_duplicated`: for every block with a non-empty caption, the caption's plain text does not equal its first half repeated twice, and the Bugbear first image caption text equals `"Level design concept I drew on paper."`.
  - `test_clean_rich_text`: `<span>a</span><script>x</script><a href="https://x.com">l</a><a href="javascript:alert(1)">j</a>` → `a<a href="https://x.com" rel="noopener" target="_blank">l</a>j`.
  - `test_unicode_roundtrip`: write and re-read a Site containing `"Ylimäki – “quote”"` via `main`'s writer; it comes back identical.

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/Scripts/python -m pytest tools/tests/test_scrape.py -v`
Expected: FAIL (ImportError: `tools.scrape`).

- [ ] **Step 4: Implement `tools/scrape.py`** to the interfaces above, using BeautifulSoup with `html.parser`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/Scripts/python -m pytest tools/tests/test_scrape.py -v`
Expected: all PASS.

- [ ] **Step 6: Generate the content**

Run: `.venv/Scripts/python -m tools.scrape`
Expected: `content/site.json` exists with 5 projects; opening it shows "Ylimäki" correctly.

- [ ] **Step 7: Commit**

```bash
git add .gitignore tools content
git commit -m "feat: scrape current portfolio into content/site.json"
```

---

### Task 2: Image pipeline

**Files:**
- Create: `tools/images.py`, `tools/tests/test_images.py`, `assets/images/<slug>/*`
- Modify: `content/site.json` (fills the image fields), `.gitignore` (already has `tools/.download/`)

**Interfaces:**
- Consumes: the `site.json` schema (Task 1).
- `download(url: str, dest: Path, session=None) -> Path`: returns immediately if `dest` exists; otherwise streams to `dest.with_suffix(dest.suffix + ".part")` with a 60s timeout, raises on non-2xx, then renames to `dest`.
- `optimise(src: Path, out_dir: Path, stem: str, max_width: int = 2000) -> dict`: returns `{ext, width, height, webp}`. Animated GIF (`getattr(im, "is_animated", False)`) or any GIF → copy the bytes to `<stem>.gif`, `webp=False`. PNG → `<stem>.png` plus `<stem>.webp`. Everything else → RGB `<stem>.jpg` (quality 85, progressive) plus `<stem>.webp` (quality 82). Downscale with LANCZOS only when wider than `max_width`; never upscale.
- `process_site(site: dict, root: Path, cache: Path, fetch=download) -> dict`: for each project, numbers images `01`, `02`, … in document order (descending into Rows) and handles the cover as `cover`. Downloads into `cache/<slug>/<stem><source-ext>`, optimises into `root/assets/images/<slug>/` and sets `file` = `assets/images/<slug>/<stem>` (POSIX), `ext`, `width`, `height`, `webp`. Covers get an Image dict built from `cover_url`. Returns the updated site.
- `main()` loads `content/site.json`, runs `process_site(site, Path("."), Path("tools/.download"))` and saves it back (utf-8, `ensure_ascii=False`).

- [ ] **Step 1: Write failing tests** in `tools/tests/test_images.py` using Pillow-generated files in `tmp_path`:
  - `test_jpeg_downscaled`: a 3000×1500 JPEG gives `{"ext":"jpg","width":2000,"height":1000,"webp":True}`, and both files exist.
  - `test_small_png_not_upscaled`: an 800×600 RGBA PNG gives `ext "png"`, width 800, and a `.webp` exists.
  - `test_animated_gif_copied`: a 2-frame GIF gives `webp False`, and the output bytes equal the input bytes.
  - `test_download_atomic_and_skips_existing`: a fake session whose response raises halfway leaves neither `dest` nor any final file (the `.part` may remain); calling again with an existing `dest` does not call the session at all.
  - `test_process_site_numbering`: a Site with blocks `[image, row[video, image], image]` plus a cover and a fake `fetch` that writes a 100×100 JPEG gives files `…/01`, `…/02`, `…/03` and `…/cover`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python -m pytest tools/tests/test_images.py -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implement `tools/images.py`** to the interfaces above.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m pytest tools/tests -v`
Expected: all PASS.

- [ ] **Step 5: Process the real images**

Run: `.venv/Scripts/python -m tools.images`
Expected: 73 numbered images plus 5 covers under `assets/images/`; every Image in `site.json` has non-null `file`, `ext`, `width` and `height`. Report `du -sh assets/images`; above 150 MB, stop and flag it before committing.

- [ ] **Step 6: Commit**

```bash
git add tools/images.py tools/tests/test_images.py assets/images content/site.json
git commit -m "feat: download and web-optimise portfolio images"
```

---

### Task 3: Page builder

**Files:**
- Create: `tools/build.py`, `tools/tests/test_build.py`, `index.html`, `casual-art.html`, `indie-stuff.html`, `bugbear-stuff.html`, `miscellaneous-stuff.html`, `aalto-university-stuff.html`

**Interfaces:**
- Consumes: the `site.json` schema with image fields filled (Task 2).
- `youtube_id(value: str) -> str`: `""` → `""`; a bare 11-character ID `[A-Za-z0-9_-]{11}` → itself; a `youtube.com/watch?v=`, `youtu.be/`, `youtube.com/shorts/` or `youtube.com/embed/` URL → its ID (query parameters ignored); anything else → `ValueError`.
- `render_page(site: dict, project: dict | None) -> str`: `None` renders the home page.
- `build(root: Path, site: dict) -> list[Path]`: writes all 6 pages with `encoding="utf-8"` and returns their paths. `main()` loads `content/site.json` and calls `build(Path("."), site)`.
- HTML contract that Task 4 (CSS) and Task 5 (JS) rely on:
  - `<header class="site-header">` with `<a class="site-name" href="index.html">` and `<p class="site-tagline">`
  - Home: `<main class="tiles">` containing `<a class="tile" href="<slug>.html">` with the image and `<span class="tile-title">`
  - Project: `<main class="project">` containing `<h1 class="project-title">`, `<div class="project-intro">` and then blocks
  - Image block: `<figure class="block block-image"><a class="lb" href="<file>.<ext>">` + `<picture>` (`<source type="image/webp" srcset="<file>.webp">` only when `webp`) + `<img src="<file>.<ext>" width height alt loading="lazy" decoding="async">` + `</a>` + `<figcaption>` only if there is a caption
  - Video block, ID set: `<figure class="block block-video"><button class="yt" type="button" data-youtube-id="ID" aria-label="Play video">` holding `<img src="https://i.ytimg.com/vi/ID/hqdefault.jpg" alt="" loading="lazy">` and `<span class="yt-play"></span>` + optional `<figcaption>`
  - Video block, no ID: `<figure class="block block-video"><div class="video-soon">Video coming soon</div>` + optional `<figcaption>`
  - Row: `<div class="block block-row">` holding its child blocks
  - Text: `<div class="block block-text">`
  - Project footer nav: `<nav class="project-nav"><a class="prev" href>← <title></a><a class="next" href><title> →</a></nav>`, wrapping around the 5 projects
  - `<footer class="site-footer">` containing `about`, a `mailto:` link if `email` is set, a LinkedIn link if `linkedin` is set, and `© <current year> Juha Ylimäki`
  - `<head>`: Google Fonts link for Montserrat 700 and Inter 400;600 with `display=swap`, `assets/css/style.css`, `<script src="assets/js/main.js" defer>`
  - Titles: home `Juha Ylimäki — Games and Visuals`; project `<title> — Juha Ylimäki`. `og:image` = `base_url + "/" + cover file + "." + ext`.
- Alt text: the caption's plain text cut to 125 characters at a word boundary, else `"<project title> — image <n>"`.

- [ ] **Step 1: Write failing tests** in `tools/tests/test_build.py` against a small in-memory Site fixture (2 projects, one image with a caption, one without, a GIF, a row, a video with an ID and one without):
  - `test_youtube_id_forms`: `"dQw4w9WgXcQ"`, `"https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s"`, `"https://youtu.be/dQw4w9WgXcQ?si=abc"`, `"https://youtube.com/shorts/dQw4w9WgXcQ"` and `"https://www.youtube.com/embed/dQw4w9WgXcQ"` all give `"dQw4w9WgXcQ"`; `""` gives `""`; `"https://vimeo.com/1"` raises `ValueError`.
  - `test_home_tiles_order_and_lazy`: tile hrefs appear in project order; the first tile's `img` has no `loading="lazy"`, the others do.
  - `test_project_nav_wraps`: on the first project, `prev` links to the last project's slug; on the last, `next` links to the first.
  - `test_picture_sources`: a JPEG with `webp: True` has a `<source type="image/webp">`; the GIF has no `<source>`; every `img` has `width` and `height`.
  - `test_image_without_caption`: no `<figcaption>` for that block; alt equals `"<title> — image <n>"`.
  - `test_video_states`: an empty ID renders "Video coming soon" and no `ytimg` URL; a set ID renders `data-youtube-id="dQw4w9WgXcQ"` and its thumbnail URL; no page contains `adobe.io`.
  - `test_footer_contact`: with an empty email there is no `mailto:`; with `email="a@b.fi"` the footer contains `href="mailto:a@b.fi"`.
  - `test_escaping`: a title `"R&D <x>"` appears as `R&amp;D &lt;x&gt;` in `<title>` and `h1`.
  - `test_build_writes_utf8`: `build(tmp_path, site)` writes 3 files (home + 2), and `index.html` read as utf-8 contains `Ylimäki`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/Scripts/python -m pytest tools/tests/test_build.py -v`
Expected: FAIL (ImportError).

- [ ] **Step 3: Implement `tools/build.py`** with `html.escape` for all text from `site.json` except `caption_html`, `description_html` and Text `html`, which are already cleaned by `clean_rich_text`. Use f-strings and no template engine.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/Scripts/python -m pytest tools/tests -v`
Expected: all PASS.

- [ ] **Step 5: Build the real pages**

Run: `.venv/Scripts/python -m tools.build`
Expected: 6 HTML files at the repo root.

- [ ] **Step 6: Commit**

```bash
git add tools/build.py tools/tests/test_build.py *.html
git commit -m "feat: generate static pages from site.json"
```

---

### Task 4: Stylesheet and visual pass

**Files:**
- Create: `assets/css/style.css`, `.claude/launch.json`

**Interfaces:**
- Consumes: the HTML contract from Task 3. The lightbox (`.lightbox`, `.lightbox img`, `.lightbox-close`, `.lightbox-prev`, `.lightbox-next`) and `.yt iframe` styles are also written here, with the class names Task 5 uses.

- [ ] **Step 1: Add a local server config** in `.claude/launch.json`: name `site`, runtime `.venv/Scripts/python`, args `["-m","http.server","8000"]`, port 8000.

- [ ] **Step 2: Write `assets/css/style.css`** using these values. Define them as custom properties: `--bg #191919`, `--text #eeeeee`, `--muted #a0a0a0`, `--max 1200px`, gutter `clamp(16px, 4vw, 48px)`.
  - Header: Montserrat 700, name 30px uppercase, tagline 12px uppercase with 0.1em letter spacing.
  - Home tiles: full column width, stacked with a 24px gap, image `aspect-ratio` from its width/height and `object-fit: cover`; the title overlays the bottom-left in Montserrat 700, `clamp(24px, 5vw, 56px)`, with a text shadow.
  - Project title Montserrat 700 `clamp(32px, 6vw, 70px)`; body Inter 16px/1.6.
  - Blocks: 48px apart. Images are `width:100%; height:auto`. Figcaptions are Inter 15px `--muted`, 12px top margin, max 70ch.
  - `.block-row`: CSS grid, `repeat(auto-fit, minmax(0,1fr))`, 24px gap; a single column below 768px.
  - `.yt` and `.video-soon`: `aspect-ratio:16/9`, full width. `.yt-play` is a centred 72px circular play icon drawn in CSS.
  - Visible `:focus-visible` outline on links and buttons.

- [ ] **Step 3: Verify in the browser pane**

Start the `site` preview. Screenshot `index.html` and `indie-stuff.html` at desktop width and at the `mobile` preset (375px). Then run in the page: `document.documentElement.scrollWidth <= innerWidth` → `true` at 375px on all 6 pages. Compare the home page side by side with `https://juhaylimaki.myportfolio.com`: same tile order, header text and dark look. The console shows no errors.

- [ ] **Step 4: Commit**

```bash
git add assets/css .claude/launch.json
git commit -m "feat: add site stylesheet"
```

---

### Task 5: Lightbox and click-to-load YouTube (`assets/js/main.js`)

**Files:**
- Create: `assets/js/main.js`

**Interfaces:**
- Consumes: `a.lb` and `button.yt[data-youtube-id]` from Task 3, and the lightbox class names from Task 4.
- Behaviour:
  - Clicking `a.lb` calls `preventDefault` and opens one shared `<div class="lightbox" role="dialog" aria-modal="true">`, appended to `body` once and shown or hidden with its `hidden` attribute. It contains the `img` (`src` = link `href`, `alt` copied), close/prev/next buttons, and sets `body.style.overflow = "hidden"`.
  - Esc, a click on the backdrop or `.lightbox-close` closes it and returns focus to the opening link. ←/→ and the prev/next buttons move between the `a.lb` elements in document order, wrapping around.
  - Clicking `button.yt` replaces the button with `<iframe src="https://www.youtube-nocookie.com/embed/ID?autoplay=1" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen title="YouTube video">`.
  - Without JS, `a.lb` still opens the image directly.

- [ ] **Step 1: Implement `assets/js/main.js`** as one IIFE with `"use strict"`, about 100 lines and no dependencies.

- [ ] **Step 2: Verify in the browser pane** on `casual-art.html` with `javascript_tool`:
  - `document.querySelectorAll('a.lb')[0].click(); document.querySelector('.lightbox')?.hidden === false` → `true`
  - dispatch `keydown` `ArrowRight`; the lightbox `img.src` ends with `/02.<ext>`
  - dispatch `keydown` `Escape`; the lightbox is hidden and `document.activeElement` is the first `a.lb`
  - since no real IDs exist yet, inject a test button with JS (`<button class="yt" data-youtube-id="dQw4w9WgXcQ">`) into `main`, click it, and check that `main iframe[src*="youtube-nocookie.com/embed/dQw4w9WgXcQ"]` exists (the click handler must therefore be delegated from `document`)
  - `read_console_messages` with `onlyErrors` returns nothing

- [ ] **Step 3: Commit**

```bash
git add assets/js/main.js
git commit -m "feat: add lightbox and click-to-load YouTube embeds"
```

---

### Task 6: Site checker, contact info, video checklist and README

**Files:**
- Create: `tools/check_site.py`, `tools/tests/test_check_site.py`, `tools/video_checklist.py`, `docs/video-checklist.md`, `README.md`
- Modify: `content/site.json` (contact), the generated `*.html`

**Interfaces:**
- `check(root: Path) -> list[str]`: for every `*.html` in `root`, each local `src`, `href` and `srcset` URL (excluding `http(s):`, `mailto:` and `#…`) must exist as a file. Every `<img>` must have `alt`, plus `width` and `height` unless its `src` starts with `https://i.ytimg.com/`. Each problem is one string, `"<page>: <problem>"`. `main()` prints them and exits 1 if there are any, else prints `OK: <n> pages`.
- `tools/video_checklist.py` `main()` writes `docs/video-checklist.md`: a section per project, with one unchecked line per video in document order: `- [ ] <n>. <caption plain text, first 80 chars or "(no caption)"> — youtube_id: <current or empty>`.

- [ ] **Step 1: Write failing tests** in `tools/tests/test_check_site.py` on a `tmp_path` site:
  - `test_clean_site_passes`: one page referencing an existing image (with alt, width, height) → `[]`.
  - `test_missing_file_and_alt`: a missing `srcset` file and an `img` without `alt` each produce one error naming the page.
  - `test_external_and_mailto_ignored`: `https://…`, `mailto:…` and `#top` produce no errors.

- [ ] **Step 2: Run tests to verify they fail**, then **implement**, then **run to verify they pass**

Run: `.venv/Scripts/python -m pytest tools/tests -v`
Expected: FAIL before implementing, then all PASS.

- [ ] **Step 3: Fill in contact info.** Ask Juha in chat for his email address and LinkedIn URL if they aren't in `site.json` yet. Set `contact.email` and `contact.linkedin`, then run `.venv/Scripts/python -m tools.build`.

- [ ] **Step 4: Generate the checklist and check the site**

Run: `.venv/Scripts/python -m tools.video_checklist` then `.venv/Scripts/python -m tools.check_site`
Expected: `docs/video-checklist.md` lists 20 videos (Casual 1, Indie 5, Bugbear 1, Freelance 10, Aalto 3); the checker prints `OK: 6 pages`.

- [ ] **Step 5: Write `README.md`**: what the site is; how to edit content (`content/site.json`); how to add a YouTube video (paste the URL into `youtube_id`, then run `.venv/Scripts/python -m tools.build`); how to preview locally (`python -m http.server 8000`); how to deploy (commit and push to `main`); and "cancel Adobe only after every video in docs/video-checklist.md is ticked and the live site is checked".

- [ ] **Step 6: Commit**

```bash
git add tools/check_site.py tools/tests/test_check_site.py tools/video_checklist.py docs/video-checklist.md README.md content/site.json *.html
git commit -m "feat: add site checker, video checklist, README and contact info"
```

---

### Task 7: Publish to GitHub Pages and final verification

**Files:** none new (adds a git remote).

- [ ] **Step 1: Juha creates the repository.** Ask Juha to sign in to (or create) a GitHub account and create an empty **public** repository named exactly `<github-username>.github.io`, then send the username. Account creation and sign-in are his to do.

- [ ] **Step 2: Push, after Juha confirms in chat**

```bash
git remote add origin https://github.com/<username>/<username>.github.io.git
git push -u origin main
```
Expected: the push succeeds (Git Credential Manager prompts Juha to sign in on first push). If the username isn't `juhaylimaki`, change `base_url` in `site.json`, rebuild, commit and push again.

- [ ] **Step 3: Enable Pages.** Juha opens Settings → Pages and sets Source to "Deploy from a branch", `main`, `/ (root)`. Within a few minutes, `https://<username>.github.io` serves the site.

- [ ] **Step 4: Verify the live site** in the browser pane: open each of the 6 pages at desktop and 375px widths and compare it to the old site page by page (block count and order, captions). Check that the lightbox works, the network panel shows no 404s and the console shows no errors.

- [ ] **Step 5: Report to Juha** with the live URL, the video checklist (20 videos still to upload), and the reminder not to cancel Adobe until the checklist is complete and the videos are live.
