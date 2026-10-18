from tools.video_checklist import render_checklist

SITE = {"projects": [
    {"slug": "a", "title": "Alpha", "blocks": [
        {"type": "video", "adobe_id": "x", "youtube_id": "", "caption_html": "<p>Trailer of the <b>game</b></p>"},
        {"type": "image", "caption_html": "<p>not a video</p>"},
        {"type": "row", "children": [
            {"type": "video", "adobe_id": "y", "youtube_id": "dQw4w9WgXcQ", "caption_html": ""},
        ]},
    ]},
    {"slug": "b", "title": "Beta", "blocks": []},
]}


def test_lists_videos_in_order_with_status():
    text = render_checklist(SITE)
    assert "## Alpha" in text
    assert "- [ ] 1. Trailer of the game — youtube_id: (empty)" in text
    assert "- [x] 2. (no caption) — youtube_id: dQw4w9WgXcQ" in text
    assert "not a video" not in text
    assert "## Beta" not in text
