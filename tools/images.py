"""Downloads the original portfolio images and writes web-sized copies.

Fills the file/ext/width/height/webp fields of every image in content/site.json.
"""
import json
import shutil
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

import requests
from PIL import Image

SITE_JSON = Path("content/site.json")
WEBP_QUALITY = 82
JPEG_QUALITY = 85


def download(url: str, dest: Path, session=None) -> Path:
    if dest.exists():
        return dest
    session = session or requests.Session()
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    with session.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with open(part, "wb") as f:
            for chunk in response.iter_content(chunk_size=1 << 16):
                f.write(chunk)
    part.replace(dest)
    return dest


def _resized(im: Image.Image, max_width: int) -> Image.Image:
    if im.width <= max_width:
        return im
    height = round(im.height * max_width / im.width)
    return im.resize((max_width, height), Image.LANCZOS)


def optimise(src: Path, out_dir: Path, stem: str, max_width: int = 2000) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        if im.format == "GIF":
            shutil.copyfile(src, out_dir / f"{stem}.gif")
            return {"ext": "gif", "width": im.width, "height": im.height, "webp": False}
        if im.format == "PNG":
            ext = "png"
            im = _resized(im, max_width)
            im.save(out_dir / f"{stem}.png", optimize=True)
        else:
            ext = "jpg"
            im = _resized(im.convert("RGB"), max_width)
            im.save(out_dir / f"{stem}.jpg", quality=JPEG_QUALITY, progressive=True, optimize=True)
        im.save(out_dir / f"{stem}.webp", quality=WEBP_QUALITY, method=6)
        return {"ext": ext, "width": im.width, "height": im.height, "webp": True}


def _images(blocks):
    for block in blocks:
        if block["type"] == "row":
            yield from _images(block["children"])
        elif block["type"] == "image":
            yield block


def _source_suffix(url: str) -> str:
    return PurePosixPath(urlparse(url).path).suffix.lower() or ".jpg"


def process_site(site: dict, root: Path, cache: Path, fetch=download) -> dict:
    for project in site["projects"]:
        slug = project["slug"]
        out_dir = root / "assets" / "images" / slug
        numbered = [(f"{n:02d}", img) for n, img in enumerate(_images(project["blocks"]), start=1)]
        for stem, image in [("cover", project["cover"]), *numbered]:
            url = image["source_url"]
            src = fetch(url, cache / slug / f"{stem}{_source_suffix(url)}")
            image.update(optimise(src, out_dir, stem))
            image["file"] = f"assets/images/{slug}/{stem}"
    return site


def main() -> None:
    site = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    process_site(site, Path("."), Path("tools/.download"))
    SITE_JSON.write_text(json.dumps(site, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    count = sum(1 for p in site["projects"] for _ in _images(p["blocks"]))
    print(f"Processed {count} images + {len(site['projects'])} covers")


if __name__ == "__main__":
    main()
