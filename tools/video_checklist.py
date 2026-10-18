"""Writes docs/video-checklist.md: every video on the site and whether it has a YouTube ID yet.

Run:  .venv/Scripts/python -m tools.video_checklist
"""
import json
from pathlib import Path

from tools.build import plain_text, shorten, youtube_id

SITE_JSON = Path("content/site.json")
OUTPUT = Path("docs/video-checklist.md")


def _videos(blocks):
    for block in blocks:
        if block["type"] == "row":
            yield from _videos(block["children"])
        elif block["type"] == "video":
            yield block


def render_checklist(site: dict) -> str:
    lines = [
        "# Video checklist",
        "",
        "Upload each video to YouTube, paste its link into the matching `youtube_id` in",
        "`content/site.json`, then run `.venv/Scripts/python -m tools.build` and",
        "`.venv/Scripts/python -m tools.video_checklist`.",
        "Cancel Adobe only when every box is ticked and the live site plays them all.",
    ]
    for project in site["projects"]:
        videos = list(_videos(project["blocks"]))
        if not videos:
            continue
        lines += ["", f"## {project['title']}", ""]
        for n, video in enumerate(videos, start=1):
            label = shorten(plain_text(video.get("caption_html", "")), 80) or "(no caption)"
            raw = video.get("youtube_id", "")
            try:
                vid = youtube_id(raw)
                status = vid or "(empty)"
            except ValueError:
                vid, status = "", f"INVALID: {raw}"
            done = "x" if vid else " "
            lines.append(f"- [{done}] {n}. {label} — youtube_id: {status}")
    return "\n".join(lines) + "\n"


def main() -> None:
    site = json.loads(SITE_JSON.read_text(encoding="utf-8"))
    OUTPUT.write_text(render_checklist(site), encoding="utf-8", newline="\n")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
