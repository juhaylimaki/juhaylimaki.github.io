"""Writes the static HTML pages from content/site.json.

Run after any change to site.json:  .venv/Scripts/python -m tools.build
"""
import datetime
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

SITE_JSON = Path("content/site.json")
FONTS = "https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Montserrat:wght@700&display=swap"
YT_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def plain_text(rich: str) -> str:
    text = re.sub(r"<br\s*/?>|</p>", " ", rich)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return re.sub(r"\s+", " ", text).strip()


def shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(" ,.;:") + "…"


def youtube_id(value: str) -> str:
    value = value.strip()
    if not value or YT_ID.match(value):
        return value
    url = urlparse(value if "://" in value else "https://" + value)
    host = url.netloc.lower()
    for prefix in ("www.", "m.", "music."):
        host = host.removeprefix(prefix)
    candidate = ""
    if host == "youtu.be":
        candidate = url.path.strip("/")
    elif host == "youtube.com" or host == "youtube-nocookie.com":
        if url.path == "/watch":
            candidate = parse_qs(url.query).get("v", [""])[0]
        else:
            parts = url.path.strip("/").split("/")
            if len(parts) == 2 and parts[0] in ("shorts", "embed", "live"):
                candidate = parts[1]
    if YT_ID.match(candidate):
        return candidate
    raise ValueError(f"not a YouTube video URL or ID: {value!r}")


def render_image(image: dict, alt: str, lazy: bool = True) -> str:
    file, ext = image["file"], image["ext"]
    loading = ' loading="lazy"' if lazy else ""
    source = f'<source type="image/webp" srcset="{file}.webp">' if image["webp"] else ""
    return (f'<picture>{source}<img src="{file}.{ext}" width="{image["width"]}" height="{image["height"]}" '
            f'alt="{esc(alt)}"{loading} decoding="async"></picture>')


def caption(block: dict) -> str:
    return f"<figcaption>{block['caption_html']}</figcaption>" if block.get("caption_html") else ""


def render_block(block: dict, project: dict, counter: list) -> str:
    kind = block["type"]
    if kind == "image":
        counter[0] += 1
        alt = shorten(plain_text(block.get("caption_html", "")), 125) or f"{project['title']} — image {counter[0]}"
        return (f'<figure class="block block-image"><a class="lb" href="{block["file"]}.{block["ext"]}">'
                f'{render_image(block, alt)}</a>{caption(block)}</figure>')
    if kind == "video":
        vid = youtube_id(block.get("youtube_id", ""))
        if vid:
            player = (f'<button class="yt" type="button" data-youtube-id="{vid}" aria-label="Play video">'
                      f'<img src="https://i.ytimg.com/vi/{vid}/hqdefault.jpg" alt="" loading="lazy">'
                      f'<span class="yt-play"></span></button>')
        else:
            player = '<div class="video-soon">Video coming soon</div>'
        return f'<figure class="block block-video">{player}{caption(block)}</figure>'
    if kind == "row":
        inner = "".join(render_block(child, project, counter) for child in block["children"])
        return f'<div class="block block-row">{inner}</div>'
    if kind == "text":
        return f'<div class="block block-text">{block["html"]}</div>'
    raise ValueError(f"unknown block type {kind!r} in {project['slug']}")


def render_header(site: dict) -> str:
    return (f'<header class="site-header"><a class="site-name" href="index.html">{esc(site["name"].upper())}</a>'
            f'<p class="site-tagline">{esc(site["tagline"].upper())}</p></header>')


def render_footer(site: dict) -> str:
    contact = site.get("contact", {})
    links = []
    if contact.get("email"):
        links.append(f'<a href="mailto:{esc(contact["email"])}">{esc(contact["email"])}</a>')
    if contact.get("linkedin"):
        links.append(f'<a href="{esc(contact["linkedin"])}" target="_blank" rel="noopener">LinkedIn</a>')
    contact_html = f'<p class="footer-contact">{" · ".join(links)}</p>' if links else ""
    year = datetime.date.today().year
    return (f'<footer class="site-footer"><p class="footer-about">{esc(site["about"])}</p>{contact_html}'
            f'<p class="footer-copy">© {year} {esc(site["name"])}</p></footer>')


def render_home(site: dict) -> str:
    tiles = []
    for i, project in enumerate(site["projects"]):
        tiles.append(f'<a class="tile" href="{project["slug"]}.html">'
                     f'{render_image(project["cover"], project["title"], lazy=i > 0)}'
                     f'<span class="tile-title">{esc(project["title"])}</span></a>')
    return f'<main class="tiles">{"".join(tiles)}</main>'


class BuildError(Exception):
    """A problem in site.json, worded so it can be fixed by hand."""


def render_project(site: dict, project: dict) -> str:
    projects = site["projects"]
    i = projects.index(project)
    prev, nxt = projects[i - 1], projects[(i + 1) % len(projects)]
    counter = [0]
    rendered = []
    for n, block in enumerate(project["blocks"], start=1):
        try:
            rendered.append(render_block(block, project, counter))
        except (KeyError, ValueError, TypeError) as e:
            problem = f"missing field {e}" if isinstance(e, KeyError) else str(e)
            raise BuildError(f'{project["slug"]}, block {n}: {problem}') from e
    blocks = "".join(rendered)
    intro = f'<div class="project-intro">{project["description_html"]}</div>' if project["description_html"] else ""
    nav = (f'<nav class="project-nav"><a class="prev" href="{prev["slug"]}.html">← {esc(prev["title"])}</a>'
           f'<a class="next" href="{nxt["slug"]}.html">{esc(nxt["title"])} →</a></nav>')
    return f'<main class="project"><h1 class="project-title">{esc(project["title"])}</h1>{intro}{blocks}{nav}</main>'


def render_page(site: dict, project: dict | None) -> str:
    if project is None:
        title = f'{site["name"]} — {site["tagline"]}'
        description = f'{site["about"]} Portfolio of {site["name"]}.'
        cover = site["projects"][0]["cover"]
        body = render_home(site)
    else:
        title = f'{project["title"]} — {site["name"]}'
        description = plain_text(project["description_html"]) or project["title"]
        cover = project["cover"]
        body = render_project(site, project)
    description = shorten(description, 155)
    og_image = f'{site["base_url"]}/{cover["file"]}.{cover["ext"]}'
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:image" content="{esc(og_image)}">
<meta property="og:type" content="website">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="assets/css/style.css">
<script src="assets/js/main.js" defer></script>
</head>
<body>
{render_header(site)}
{body}
{render_footer(site)}
</body>
</html>
"""


def build(root: Path, site: dict) -> list[Path]:
    pages = [(root / "index.html", None)] + [(root / f'{p["slug"]}.html', p) for p in site["projects"]]
    rendered = [(path, render_page(site, project)) for path, project in pages]  # all or nothing
    for path, page in rendered:
        path.write_text(page, encoding="utf-8", newline="\n")
    return [path for path, _ in rendered]


def main() -> None:
    try:
        site = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"{SITE_JSON} is not valid JSON (line {e.lineno}, column {e.colno}): {e.msg}. Nothing was written.")
    try:
        written = build(Path("."), site)
    except BuildError as e:
        sys.exit(f"Error in {SITE_JSON}: {e}. Nothing was written.")
    for path in written:
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
