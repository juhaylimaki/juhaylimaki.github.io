from pathlib import Path

import pytest
from PIL import Image

from tools.images import download, optimise, process_site


def make_jpeg(path: Path, size=(100, 100)):
    Image.new("RGB", size, (200, 80, 40)).save(path, "JPEG")
    return path


def test_jpeg_downscaled(tmp_path):
    src = make_jpeg(tmp_path / "big.jpg", (3000, 1500))
    out = tmp_path / "out"
    info = optimise(src, out, "01")
    assert info == {"ext": "jpg", "width": 2000, "height": 1000, "webp": True}
    assert Image.open(out / "01.jpg").size == (2000, 1000)
    assert Image.open(out / "01.webp").size == (2000, 1000)


def test_small_png_not_upscaled(tmp_path):
    src = tmp_path / "small.png"
    Image.new("RGBA", (800, 600), (0, 0, 0, 0)).save(src)
    info = optimise(src, tmp_path / "out", "02")
    assert info == {"ext": "png", "width": 800, "height": 600, "webp": True}
    assert (tmp_path / "out" / "02.webp").exists()


def test_animated_gif_copied(tmp_path):
    src = tmp_path / "anim.gif"
    frames = [Image.new("P", (50, 40), i) for i in (1, 2)]
    frames[0].save(src, save_all=True, append_images=frames[1:], duration=100, loop=0)
    info = optimise(src, tmp_path / "out", "03")
    assert info == {"ext": "gif", "width": 50, "height": 40, "webp": False}
    assert (tmp_path / "out" / "03.gif").read_bytes() == src.read_bytes()
    assert not (tmp_path / "out" / "03.webp").exists()


class BrokenResponse:
    status_code = 200

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        yield b"partial-bytes"
        raise ConnectionError("network dropped")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def get(self, url, stream, timeout):
        self.calls += 1
        return self.response


def test_download_atomic_and_skips_existing(tmp_path):
    dest = tmp_path / "img.jpg"
    session = FakeSession(BrokenResponse())
    with pytest.raises(ConnectionError):
        download("https://example.com/a.jpg", dest, session=session)
    assert not dest.exists()

    dest.write_bytes(b"complete")
    session = FakeSession(BrokenResponse())
    assert download("https://example.com/a.jpg", dest, session=session) == dest
    assert session.calls == 0


def image_block(url):
    return {"type": "image", "source_url": url, "caption_html": "",
            "file": None, "ext": None, "width": None, "height": None, "webp": None}


def test_process_site_numbering(tmp_path):
    site = {"projects": [{
        "slug": "demo",
        "cover": image_block("https://x/cover.jpg"),
        "blocks": [
            image_block("https://x/a.jpg"),
            {"type": "row", "children": [
                {"type": "video", "adobe_id": "v", "youtube_id": "", "caption_html": ""},
                image_block("https://x/b.jpg"),
            ]},
            image_block("https://x/c.jpg?h=123"),
        ],
    }]}

    def fake_fetch(url, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        return make_jpeg(dest)

    result = process_site(site, tmp_path, tmp_path / "cache", fetch=fake_fetch)
    project = result["projects"][0]
    blocks = project["blocks"]
    assert [blocks[0]["file"], blocks[1]["children"][1]["file"], blocks[2]["file"]] == [
        "assets/images/demo/01", "assets/images/demo/02", "assets/images/demo/03"]
    assert project["cover"]["file"] == "assets/images/demo/cover"
    assert blocks[2]["ext"] == "jpg" and blocks[2]["width"] == 100
    assert (tmp_path / "assets/images/demo/03.webp").exists()
