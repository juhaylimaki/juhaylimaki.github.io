from tools.check_site import check


def page(body):
    return f'<!doctype html><html><head><link rel="stylesheet" href="style.css"></head><body>{body}</body></html>'


def test_clean_site_passes(tmp_path):
    (tmp_path / "style.css").write_text("", encoding="utf-8")
    (tmp_path / "a.jpg").write_bytes(b"x")
    (tmp_path / "a.webp").write_bytes(b"x")
    (tmp_path / "index.html").write_text(page(
        '<picture><source srcset="a.webp"><img src="a.jpg" alt="A" width="1" height="1"></picture>'
        '<a href="index.html">home</a>'), encoding="utf-8")
    assert check(tmp_path) == []


def test_missing_file_and_alt(tmp_path):
    (tmp_path / "style.css").write_text("", encoding="utf-8")
    (tmp_path / "a.jpg").write_bytes(b"x")
    (tmp_path / "index.html").write_text(page(
        '<source srcset="missing.webp"><img src="a.jpg" width="1" height="1">'), encoding="utf-8")
    errors = check(tmp_path)
    assert len(errors) == 2
    assert all(e.startswith("index.html: ") for e in errors)
    assert any("missing.webp" in e for e in errors)
    assert any("alt" in e for e in errors)


def test_missing_dimensions_except_youtube_thumbs(tmp_path):
    (tmp_path / "style.css").write_text("", encoding="utf-8")
    (tmp_path / "a.jpg").write_bytes(b"x")
    (tmp_path / "index.html").write_text(page(
        '<img src="a.jpg" alt="A"><img src="https://i.ytimg.com/vi/x/hqdefault.jpg" alt="">'), encoding="utf-8")
    errors = check(tmp_path)
    assert errors == ["index.html: <img src=a.jpg> missing width/height"]


def test_external_and_mailto_ignored(tmp_path):
    (tmp_path / "style.css").write_text("", encoding="utf-8")
    (tmp_path / "index.html").write_text(page(
        '<a href="https://example.com/x">x</a><a href="mailto:a@b.fi">m</a><a href="#top">t</a>'
        '<a href="//cdn.example.com/y">y</a>'), encoding="utf-8")
    assert check(tmp_path) == []


def test_publishing_files_required(tmp_path):
    from tools.check_site import check_publishing
    assert len(check_publishing(tmp_path)) == 2
    (tmp_path / ".nojekyll").write_text("", encoding="utf-8")
    (tmp_path / "robots.txt").write_text("User-agent: *\nDisallow: /tools/\nDisallow: /docs/\n", encoding="utf-8")
    assert check_publishing(tmp_path) == []
