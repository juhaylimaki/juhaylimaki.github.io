import json
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from tools.scrape import SLUGS, clean_rich_text, parse_home, parse_project, write_site

FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name):
    return (FIXTURES / f"{name}.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def projects():
    return {slug: parse_project(fixture(slug), slug) for slug in SLUGS}


def walk(blocks):
    for block in blocks:
        if block["type"] == "row":
            yield from walk(block["children"])
        else:
            yield block


def plain(html):
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)


def test_home_tiles():
    tiles = parse_home(fixture("work"))
    assert [t["slug"] for t in tiles] == [
        "casual-art", "indie-stuff", "bugbear-stuff",
        "miscellaneous-stuff", "aalto-university-stuff",
    ]
    assert all(t["cover_url"].startswith("https://cdn.myportfolio.com/") for t in tiles)


def test_bugbear_blocks(projects):
    p = projects["bugbear-stuff"]
    assert p["title"] == "AAA Level Designer at Bugbear Entertainment"
    assert [b["type"] for b in p["blocks"]] == ["video", "image", "image", "image", "image", "image"]
    assert p["blocks"][0]["adobe_id"] == "SgRdi4Y5_Cc"
    assert plain(p["description_html"]).startswith("Worked as a Level Designer")


def test_totals(projects):
    blocks = [b for p in projects.values() for b in walk(p["blocks"])]
    assert sum(b["type"] == "image" for b in blocks) == 73
    assert sum(b["type"] == "video" for b in blocks) == 20


def test_misc_row(projects):
    rows = [b for b in projects["miscellaneous-stuff"]["blocks"] if b["type"] == "row"]
    assert len(rows) == 1
    assert len(rows[0]["children"]) >= 2
    assert all(c["type"] == "video" for c in rows[0]["children"])


def test_original_image_url(projects):
    for p in projects.values():
        for b in walk(p["blocks"]):
            if b["type"] == "image":
                assert b["source_url"].startswith("https://")
                assert "_rw_" not in b["source_url"]


def test_captions_not_duplicated(projects):
    for p in projects.values():
        for b in walk(p["blocks"]):
            text = plain(b.get("caption_html", ""))
            if text:
                half = len(text) // 2
                assert text != (text[:half] + " " + text[:half]).strip() or len(text) < 2
                assert text.count(text[: min(40, len(text))]) == 1
    assert plain(projects["bugbear-stuff"]["blocks"][1]["caption_html"]) == "Level design concept I drew on paper."


def test_clean_rich_text():
    dirty = '<span>a</span><script>x</script><a href="https://x.com">l</a><a href="javascript:alert(1)">j</a>'
    assert clean_rich_text(dirty) == 'a<a href="https://x.com" rel="noopener" target="_blank">l</a>j'


def test_unicode_roundtrip(tmp_path):
    site = {"name": "Ylimäki – “quote”", "projects": []}
    out = tmp_path / "site.json"
    write_site(site, out)
    assert json.loads(out.read_text(encoding="utf-8")) == site
    assert "Ylimäki" in out.read_text(encoding="utf-8")
