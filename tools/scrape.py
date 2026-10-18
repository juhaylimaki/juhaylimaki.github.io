"""One-off scraper: turns the old Adobe Portfolio pages into content/site.json.

Reads the saved pages in tools/tests/fixtures/ (refresh them with curl if the
old site changes) so the result is reproducible.
"""
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

FIXTURES = Path(__file__).parent / "tests" / "fixtures"
OUTPUT = Path("content/site.json")
SLUGS = ["casual-art", "indie-stuff", "bugbear-stuff", "miscellaneous-stuff", "aalto-university-stuff"]

KEEP_TAGS = {"a", "br", "p", "strong", "b", "em", "i"}
DROP_TAGS = {"script", "style"}
MODULE = "js-js-project-module"


def clean_rich_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(DROP_TAGS):
        tag.decompose()
    for tag in soup.find_all(True):
        if tag.name not in KEEP_TAGS:
            tag.unwrap()
            continue
        href = tag.get("href", "") if tag.name == "a" else ""
        tag.attrs = {}
        if tag.name == "a":
            if href.startswith(("http://", "https://")):
                tag.attrs = {"href": href, "rel": "noopener", "target": "_blank"}
            elif href.startswith("mailto:"):
                tag.attrs = {"href": href}
            else:
                tag.unwrap()
    return str(soup).strip()


def _inner(tag) -> str:
    return "".join(str(c) for c in tag.contents) if tag else ""


def _caption(module) -> str:
    cap = module.select_one(".module-caption")
    return clean_rich_text(_inner(cap)) if cap else ""


def _top_modules(root):
    """Project modules under root that are not nested inside another module."""
    found = []
    for el in root.find_all(class_=MODULE):
        parent = el.find_parent(class_=MODULE)
        if parent is None or parent is root:
            found.append(el)
    return found


def _image(module) -> dict:
    lightbox = module.select_one(".js-lightbox")
    img = module.select_one("img")
    url = (lightbox.get("data-src") if lightbox else None) or img.get("data-src") or img.get("src")
    return {"type": "image", "source_url": url, "caption_html": _caption(module),
            "file": None, "ext": None, "width": None, "height": None, "webp": None}


def _video(module) -> dict:
    src = module.select_one("iframe")["src"]
    match = re.search(r"/ccv/([^/]+)/embed", src)
    if not match:
        raise ValueError(f"unrecognised video embed {src}")
    return {"type": "video", "adobe_id": match.group(1), "youtube_id": "", "caption_html": _caption(module)}


def _block(module, slug: str) -> dict:
    classes = module.get("class", [])
    kind = next((c for c in classes if c.startswith("project-module-")), None)
    if kind == "project-module-image":
        return _image(module)
    if kind == "project-module-video":
        return _video(module)
    if kind == "project-module-tree":
        return {"type": "row", "children": [_block(m, slug) for m in _top_modules(module)]}
    if kind == "project-module-text":
        return {"type": "text", "html": clean_rich_text(_inner(module.select_one(".rich-text") or module))}
    raise ValueError(f"unknown module {kind or classes} on {slug}")


def parse_project(html: str, slug: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    header = soup.select_one(".page-header")
    title = header.select_one(".title").get_text(strip=True)
    description = header.select_one(".description")
    main = soup.select_one("main")
    return {
        "slug": slug,
        "title": title,
        "description_html": clean_rich_text(_inner(description)) if description else "",
        "cover": None,
        "blocks": [_block(m, slug) for m in _top_modules(main)],
    }


def parse_home(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    tiles = []
    for a in soup.select("main a.project-cover"):
        img = a.select_one("img")
        url = img.get("data-src") or ""
        if not url.startswith("http"):
            url = img.get("src", "")
        title = a.select_one(".title")
        tiles.append({
            "slug": a["href"].strip("/"),
            "title": (title or a).get_text(" ", strip=True),
            "cover_url": url,
        })
    return tiles


def write_site(site: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(site, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    def read(name):
        return (FIXTURES / f"{name}.html").read_text(encoding="utf-8")

    projects = []
    for tile in parse_home(read("work")):
        project = parse_project(read(tile["slug"]), tile["slug"])
        project["cover"] = {"type": "image", "source_url": tile["cover_url"], "caption_html": "",
                            "file": None, "ext": None, "width": None, "height": None, "webp": None}
        projects.append(project)
    site = {
        "name": "Juha Ylimäki",
        "tagline": "Games and Visuals",
        "base_url": "https://juhaylimaki.github.io",
        "about": "Game artist, animator, level designer and game designer.",
        "contact": {"email": "", "linkedin": ""},
        "projects": projects,
    }
    write_site(site, OUTPUT)
    print(f"Wrote {OUTPUT} with {len(projects)} projects")


if __name__ == "__main__":
    main()
