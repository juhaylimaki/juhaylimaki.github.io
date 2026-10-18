import copy
import re

import pytest

from tools.build import build, render_page, youtube_id

YT = "dQw4w9WgXcQ"


def img(file, ext="jpg", caption="", webp=True):
    return {"type": "image", "source_url": "https://x", "caption_html": caption,
            "file": file, "ext": ext, "width": 1200, "height": 800, "webp": webp}


SITE = {
    "name": "Juha Ylimäki",
    "tagline": "Games and Visuals",
    "base_url": "https://juhaylimaki.github.io",
    "about": "Game artist.",
    "contact": {"email": "", "linkedin": ""},
    "projects": [
        {
            "slug": "first", "title": "First Project", "description_html": "<p>Intro</p>",
            "cover": img("assets/images/first/cover"),
            "blocks": [
                img("assets/images/first/01", caption="<p>A painted forest scene</p>"),
                img("assets/images/first/02"),
                img("assets/images/first/03", ext="gif", webp=False),
                {"type": "row", "children": [
                    {"type": "video", "adobe_id": "a", "youtube_id": YT, "caption_html": "<p>Trailer</p>"},
                    {"type": "video", "adobe_id": "b", "youtube_id": "", "caption_html": ""},
                ]},
                {"type": "text", "html": "<p>Some text</p>"},
            ],
        },
        {
            "slug": "second", "title": "Second", "description_html": "",
            "cover": img("assets/images/second/cover"),
            "blocks": [],
        },
    ],
}


def first():
    return SITE["projects"][0]


@pytest.mark.parametrize("value", [
    YT,
    f"https://www.youtube.com/watch?v={YT}&t=30s",
    f"https://youtu.be/{YT}?si=abc",
    f"https://youtube.com/shorts/{YT}",
    f"https://www.youtube.com/embed/{YT}",
])
def test_youtube_id_forms(value):
    assert youtube_id(value) == YT


def test_youtube_id_empty_and_invalid():
    assert youtube_id("") == ""
    with pytest.raises(ValueError):
        youtube_id("https://vimeo.com/1")


def test_home_tiles_order_and_lazy():
    html = render_page(SITE, None)
    hrefs = re.findall(r'<a class="tile" href="([^"]+)"', html)
    assert hrefs == ["first.html", "second.html"]
    tiles = re.findall(r'<a class="tile".*?</a>', html, re.S)
    assert 'loading="lazy"' not in tiles[0]
    assert 'loading="lazy"' in tiles[1]


def test_project_nav_wraps():
    html_first = render_page(SITE, SITE["projects"][0])
    html_last = render_page(SITE, SITE["projects"][-1])
    assert re.search(r'<a class="prev" href="second.html">', html_first)
    assert re.search(r'<a class="next" href="first.html">', html_last)


def test_picture_sources():
    html = render_page(SITE, first())
    figures = re.findall(r'<figure class="block block-image">.*?</figure>', html, re.S)
    assert '<source type="image/webp" srcset="assets/images/first/01.webp">' in figures[0]
    gif = next(f for f in figures if "03.gif" in f)
    assert "<source" not in gif
    for tag in re.findall(r"<img [^>]*>", html):
        if "i.ytimg.com" not in tag:
            assert 'width="' in tag and 'height="' in tag


def test_image_without_caption():
    html = render_page(SITE, first())
    figure = next(f for f in re.findall(r'<figure class="block block-image">.*?</figure>', html, re.S)
                  if "02.jpg" in f)
    assert "<figcaption" not in figure
    assert 'alt="First Project — image 2"' in figure


def test_image_alt_from_caption():
    html = render_page(SITE, first())
    assert 'alt="A painted forest scene"' in html


def test_video_states():
    html = render_page(SITE, first())
    assert f'data-youtube-id="{YT}"' in html
    assert f"https://i.ytimg.com/vi/{YT}/hqdefault.jpg" in html
    assert html.count("Video coming soon") == 1
    assert '<div class="block block-row">' in html
    assert "adobe.io" not in html


def test_footer_contact():
    assert "mailto:" not in render_page(SITE, None)
    site = copy.deepcopy(SITE)
    site["contact"] = {"email": "a@b.fi", "linkedin": "https://www.linkedin.com/in/x"}
    html = render_page(site, None)
    assert 'href="mailto:a@b.fi"' in html
    assert 'href="https://www.linkedin.com/in/x"' in html


def test_escaping():
    site = copy.deepcopy(SITE)
    site["projects"][0]["title"] = "R&D <x>"
    html = render_page(site, site["projects"][0])
    assert "<title>R&amp;D &lt;x&gt; — Juha Ylimäki</title>" in html
    assert '<h1 class="project-title">R&amp;D &lt;x&gt;</h1>' in html


def test_head_meta():
    html = render_page(SITE, first())
    assert '<meta charset="utf-8">' in html
    assert '<html lang="en">' in html
    assert '<meta property="og:image" content="https://juhaylimaki.github.io/assets/images/first/cover.jpg">' in html
    assert "<title>Juha Ylimäki — Games and Visuals</title>" in render_page(SITE, None)


def test_favicon_linked():
    assert '<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">' in render_page(SITE, None)


def test_build_writes_utf8(tmp_path):
    written = build(tmp_path, SITE)
    assert sorted(p.name for p in written) == ["first.html", "index.html", "second.html"]
    assert "Ylimäki" in (tmp_path / "index.html").read_text(encoding="utf-8")
    assert b"\r\n" not in (tmp_path / "index.html").read_bytes()


@pytest.mark.parametrize("value", [
    f"youtu.be/{YT}",
    f"www.youtube.com/watch?v={YT}",
    f"https://music.youtube.com/watch?v={YT}",
])
def test_youtube_id_schemeless_and_music(value):
    assert youtube_id(value) == YT


def test_build_error_names_location_and_writes_nothing(tmp_path):
    from tools.build import BuildError
    site = copy.deepcopy(SITE)
    site["projects"][1]["blocks"] = [{"type": "video", "adobe_id": "z", "youtube_id": "oops", "caption_html": "<p>Teaser</p>"}]
    with pytest.raises(BuildError) as err:
        build(tmp_path, site)
    assert "second" in str(err.value) and "block 1" in str(err.value) and "oops" in str(err.value)
    assert list(tmp_path.glob("*.html")) == []


def test_block_missing_optional_caption_renders():
    site = copy.deepcopy(SITE)
    site["projects"][0]["blocks"] = [{"type": "video", "youtube_id": ""}]
    assert "Video coming soon" in render_page(site, site["projects"][0])


def test_footer_obfuscated_email_is_plain_text():
    site = copy.deepcopy(SITE)
    site["contact"] = {"email": "juha.ylimaki(at)gmail.com", "linkedin": ""}
    html = render_page(site, None)
    assert '<span class="footer-email">juha.ylimaki(at)gmail.com</span>' in html
    assert "mailto:" not in html
