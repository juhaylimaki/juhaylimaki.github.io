"""Checks the built pages: every local file they reference exists, every image has alt text and dimensions.

Run:  .venv/Scripts/python -m tools.check_site
"""
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

YOUTUBE_THUMBS = "https://i.ytimg.com/"


def _is_local(url: str) -> bool:
    return bool(url) and not url.startswith(("#", "mailto:", "//", "data:")) and not urlparse(url).scheme


def _urls(tag) -> list[str]:
    urls = [tag.get(attr) for attr in ("src", "href") if tag.get(attr)]
    if tag.get("srcset"):
        urls += [part.strip().split(" ")[0] for part in tag["srcset"].split(",") if part.strip()]
    return urls


def check(root: Path) -> list[str]:
    errors = []
    for page in sorted(root.glob("*.html")):
        soup = BeautifulSoup(page.read_text(encoding="utf-8"), "html.parser")
        for tag in soup.find_all(True):
            for url in _urls(tag):
                if _is_local(url):
                    target = root / unquote(urlparse(url).path)
                    if not target.is_file():
                        errors.append(f"{page.name}: missing file {url}")
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if not img.has_attr("alt"):
                errors.append(f"{page.name}: <img src={src}> missing alt")
            if not src.startswith(YOUTUBE_THUMBS) and not (img.get("width") and img.get("height")):
                errors.append(f"{page.name}: <img src={src}> missing width/height")
    return errors


def check_publishing(root: Path) -> list[str]:
    """GitHub Pages must serve the files as-is and keep tools/ and docs/ out of search engines."""
    errors = []
    if not (root / ".nojekyll").is_file():
        errors.append(".nojekyll missing (GitHub Pages would run Jekyll and publish docs/*.md as pages)")
    robots = root / "robots.txt"
    text = robots.read_text(encoding="utf-8") if robots.is_file() else ""
    if "Disallow: /tools/" not in text or "Disallow: /docs/" not in text:
        errors.append("robots.txt must disallow /tools/ and /docs/")
    return errors


def main() -> None:
    root = Path(".")
    errors = check(root) + check_publishing(root)
    for error in errors:
        print(error)
    if errors:
        sys.exit(1)
    print(f"OK: {len(list(root.glob('*.html')))} pages")


if __name__ == "__main__":
    main()
