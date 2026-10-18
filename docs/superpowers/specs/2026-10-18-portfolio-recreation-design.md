# Portfolio Recreation — Design

**Date:** 2026-10-18
**Owner:** Juha Ylimäki
**Goal:** Recreate the portfolio at `https://juhaylimaki.myportfolio.com` as a self-owned static site so the Adobe subscription can be cancelled without the portfolio going offline.

## Decisions

| Topic | Decision |
|---|---|
| Tech | Plain HTML + CSS + a small amount of vanilla JS. No framework and no runtime dependencies; GitHub Pages serves the committed HTML as-is. |
| Content source | Content lives in `content/site.json`. A small Python script (`tools/build.py`) writes the 6 HTML pages from it, and the generated HTML is committed. To edit the site: change `site.json`, run the script, commit. |
| Hosting | GitHub Pages, free address `https://juhaylimaki.github.io` (custom domain can be added later without changes to the site). |
| Videos | Juha uploads his original video files to YouTube (unlisted or public); the site embeds them. |
| Images | Downloaded from the current site at the largest size it serves (3840px), then resized for the web. |
| Look | Faithful to the current site, plus light polish (listed below). |
| Footer contact | Email and LinkedIn; Juha supplies the exact addresses before implementation finishes. |

## Current site inventory

Home page (`/work`): header "JUHA YLIMÄKI / GAMES AND VISUALS", then 5 large project tiles (cover image + title). There is no separate hero; the first tile (Casual Art's waterfall) is what greets visitors.

Project pages are a list of modules: image (73, of which 65 JPG, 6 PNG, 2 animated GIF), video (20) and one side-by-side row of videos (on Freelance). Each image module's lightbox link holds the original full-size file. Captions are rich text with links (e.g. Steam, YouTube, game websites).

| Project page (current slug) | Images | Videos |
|---|---|---|
| Casual Art (`casual-art`) | 13 | 1 |
| Indie Games at Muro Studios (`indie-stuff`) | 35 | 5 |
| AAA Level Designer at Bugbear Entertainment (`bugbear-stuff`) | 5 | 1 |
| Freelance Illustrations and Animations (`miscellaneous-stuff`) | 13 | 10 |
| Master's Degree at Aalto University (`aalto-university-stuff`) | 7 | 3 |

Total: about 73 images and 20 videos. All videos currently play through Adobe's player (`www-ccv.adobe.io`), which will stop working when the subscription ends.

## Site structure

```
/
├── index.html                  home: header, hero, 5 project tiles, footer
├── casual-art.html
├── indie-stuff.html
├── bugbear-stuff.html
├── miscellaneous-stuff.html
├── aalto-university-stuff.html
├── assets/
│   ├── css/style.css           one shared stylesheet
│   ├── js/main.js              lightbox + YouTube click-to-load
│   └── images/<project-slug>/  web-optimised images per project
├── content/site.json           all text, captions, image metadata, YouTube IDs, contact info
├── tools/                      Python: scraper (one-off), image optimiser, page builder, site checker
├── README.md                   how to edit, rebuild and deploy
└── docs/                       this spec and the implementation plan
```

Page slugs stay the same as today so the page names map one-to-one with the old site.

## Page anatomy

**Shared header** on every page: "JUHA YLIMÄKI" (links home) and the tagline "GAMES AND VISUALS", white uppercase on a dark background.

**Home page:** the 5 project tiles in the current order, using the current cover crops. Each tile shows the project's cover image and title and links to its page.

**Project page:** title, intro paragraph, then a single column of content blocks in the same order as the current site. A block is one of:
- an image with an optional caption below it
- a YouTube video (16:9) with an optional caption below it
- a text paragraph
- a row: 2+ of the above side by side, stacking into one column below 768px

Text, captions, links and ordering are copied word-for-word from the current site. Caption HTML is reduced to `a[href]`, `br`, `strong`/`b`, `em`/`i` and `p`; other tags are unwrapped to their text. Links open in a new tab with `rel="noopener"`.

At the bottom of each project page, previous/next project links, wrapping around the 5 projects in home-page order.

**Shared footer** on every page: a short About line, the email (as a `mailto:` link) and LinkedIn, and a copyright line.

## Visual style

- Background `#191919` (the colour used by the current site), light text, generous spacing.
- Content column with a maximum width of about 1200px, centred. Images fill the column width.
- Header font: a free Google Font close to the current bold uppercase look. Body text: a clean sans-serif.
- Responsive: one column at every width; the home tiles stack on narrow screens. No horizontal scrolling at 375px wide.

## Light polish (new compared to the current site)

1. **Lightbox:** clicking an image opens it full-screen over a dark overlay. Close it with Esc, a click outside the image or the close button; the left/right arrow keys move between images on the same page.
2. **Web-optimised images:** each image is resized to at most 2000px wide and saved as WebP (quality 82), plus a JPEG/PNG fallback at the same size, served with `<picture>`. Animated GIFs are copied unchanged (no resize, no WebP) so they keep animating. The lightbox shows the same 2000px image. Images use `loading="lazy"` (except the first home tile) and explicit `width`/`height` attributes to prevent layout shift.
3. **Light YouTube embeds:** each video first shows its YouTube thumbnail with a play button, and the real `youtube-nocookie.com` iframe loads only on click. This keeps pages fast with 10 videos on one page.
4. **Previous/next project navigation** at the bottom of project pages.
5. **Footer** with About and contact info.
6. **Basic SEO:** a `<title>` and meta description on every page, plus Open Graph tags (title, description, image) so shared links show a preview.

## Videos: placeholder until uploaded

Each video block in `site.json` has a `youtube_id` (empty until uploaded). An empty ID renders a neutral "Video coming soon" panel with the caption, and the page still works. When he sends the YouTube links, the IDs are filled in and the pages are rebuilt. `youtube_id` also accepts a full YouTube URL (`watch?v=`, `youtu.be/`, `shorts/`), from which the ID is extracted.

Before the videos come down from Adobe, Juha matches each of the 20 videos to its original file. The implementation creates `docs/video-checklist.md`, listing each video by page, position and caption so he can tick them off as he uploads.

## Content migration

A one-off script in `tools/` reads the 5 project pages and the home page of the current site and:
1. Downloads every image at its largest served size into a temporary folder (not committed).
2. Records the text, captions and block order per page.

The images are then resized/converted into `assets/images/<slug>/` with predictable names (`01.webp`, `01.jpg`, …; covers as `cover.*`), and the recorded content is saved to `content/site.json`. The scraper runs once; after that `site.json` is the source of truth.

**Fonts:** the current site uses an Adobe Fonts typeface that cannot be used without the subscription. Replacements are Google Fonts: Montserrat 700 for the name and project titles, Inter 400/600 for body text and captions.

## Deployment

1. Juha creates a GitHub account (if he does not have one) and a public repository named `juhaylimaki.github.io`.
2. Push this project to it; GitHub Pages serves it at `https://juhaylimaki.github.io`.
3. Juha checks the live site, then cancels Adobe only once every page and video works on the new site.

## Testing

- Open every page in the browser at desktop (1280px) and phone (375px) widths, and compare it side by side with the current site for content and order.
- An automated link/image check (a small script in `tools/`) confirms every local image and internal link resolves; it must report zero failures.
- Lightbox: open, keyboard navigation, close (Esc, click outside, button).
- Videos: a placeholder block renders correctly; once an ID is set, click-to-load plays the video.
- No console errors on any page.

## Out of scope

- A CMS or admin interface; content is edited in `content/site.json`.
- A contact form (email link only).
- Analytics.
- A custom domain (can be added later).
- Redirects from the old `myportfolio.com` URLs (Adobe controls that domain).
