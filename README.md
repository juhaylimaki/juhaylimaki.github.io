# Juha Ylimäki — Portfolio

The source for Juha Ylimäki's games and visuals portfolio, served for free by GitHub Pages. It replaces the old Adobe Portfolio site (`juhaylimaki.myportfolio.com`).

The site is plain HTML, CSS and a little JavaScript. GitHub Pages serves the files in this repository exactly as they are, with no build step on the server.

## How it fits together

| Path | What it is |
|---|---|
| `content/site.json` | **All the content**: project titles, texts, captions, image info, YouTube IDs, footer contact details. Edit this. |
| `*.html` | The 6 pages. **Generated** from `site.json`, so don't edit them by hand. |
| `assets/css/style.css` | All styling (colours, fonts, layout). |
| `assets/js/main.js` | Click-to-enlarge lightbox and click-to-play YouTube videos. |
| `assets/images/<project>/` | Web-sized images (`01.jpg` + `01.webp`, …, `cover.*`). |
| `tools/` | Python scripts: page builder, site checker, video checklist, and the one-off migration scripts. |
| `docs/video-checklist.md` | The 20 videos still to move from Adobe to YouTube. |

## One-time setup (for editing)

You need Python 3 installed. From this folder:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r tools/requirements.txt
```

## Editing content

1. Change `content/site.json`, for example a caption or the footer `contact` email or LinkedIn link.
2. Rebuild the pages and check them:

   ```bash
   .venv/Scripts/python -m tools.build
   .venv/Scripts/python -m tools.check_site
   ```
3. Preview locally with `.venv/Scripts/python -m http.server 8000`, then open http://localhost:8000.
4. Commit and push to `main`. GitHub Pages publishes the change within a minute or two.

## Adding a YouTube video

1. Upload the video to YouTube (public or unlisted).
2. In `content/site.json`, find the video by its caption and paste the YouTube link into its `"youtube_id"`. A full link (`https://youtu.be/…`, `https://www.youtube.com/watch?v=…`) or the bare 11-character ID both work.
3. Run `.venv/Scripts/python -m tools.build` and `.venv/Scripts/python -m tools.video_checklist`, then commit and push.

Until a video has an ID, its spot shows "Video coming soon".

## Adding images

Put the web-sized image (max 2000px wide) and a `.webp` copy in `assets/images/<project>/`. Then add an image block to that project in `site.json` with `file`, `ext`, `width`, `height`, `webp` and `caption_html`, using an existing image block as the template. `tools/images.py` has `optimise()`, which makes both files from an original.

## Before cancelling Adobe

Cancel the Adobe subscription **only after** every box in `docs/video-checklist.md` is ticked and the live site plays all the videos. The videos on the old site stop working when the subscription ends.

## Tests

```bash
.venv/Scripts/python -m pytest tools/tests -q
```
