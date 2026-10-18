# Portfolio Recreation — Design

**Date:** 2026-10-18
**Owner:** Juha Ylimäki
**Goal:** Recreate the portfolio at `https://juhaylimaki.myportfolio.com` as a self-owned static site so the Adobe subscription can be cancelled without the portfolio going offline.

## Decisions

| Topic | Decision |
|---|---|
| Tech | Plain HTML + CSS + a small amount of vanilla JS. No framework, no build step, no dependencies. |
| Hosting | GitHub Pages, free address `https://juhaylimaki.github.io` (custom domain can be added later without changes to the site). |
| Videos | Juha uploads his original video files to YouTube (unlisted or public); the site embeds them. |
| Images | Downloaded from the current site at the largest size it serves (3840px), then resized for the web. |
| Look | Faithful to the current site, plus light polish (listed below). |
| Footer contact | Email and LinkedIn; Juha supplies the exact addresses before implementation finishes. |

## Current site inventory

Home page (`/work`): header "JUHA YLIMÄKI / GAMES AND VISUALS" over a full-width hero image, then 5 project tiles.

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
├── tools/                      one-off scripts used to migrate content (not linked from the site)
└── docs/                       this spec and the implementation plan
```

Page slugs stay the same as today so the page names map one-to-one with the old site.

## Page anatomy

**Shared header** on every page: "JUHA YLIMÄKI" (links home) and the tagline "GAMES AND VISUALS", white uppercase on a dark background.

**Home page:** a hero image, then the 5 project tiles in the current order. Each tile shows the project's cover image and title and links to its page.

**Project page:** title, intro paragraph, then a single column of content blocks in the same order as the current site. A block is one of:
- an image with an optional caption below it
- a YouTube video (16:9) with an optional caption below it
- a text paragraph

Text, captions, links and ordering are copied word-for-word from the current site.

At the bottom of each project page, previous/next project links, wrapping around the 5 projects in home-page order.

**Shared footer** on every page: a short About line, the email (as a `mailto:` link) and LinkedIn, and a copyright line.

## Visual style

- Background `#191919` (the colour used by the current site), light text, generous spacing.
- Content column with a maximum width of about 1200px, centred. Images fill the column width.
- Header font: a free Google Font close to the current bold uppercase look. Body text: a clean sans-serif.
- Responsive: one column at every width; the home tiles stack on narrow screens. No horizontal scrolling at 375px wide.

## Light polish (new compared to the current site)

1. **Lightbox:** clicking an image opens it full-screen over a dark overlay. Close it with Esc, a click outside the image or the close button; the left/right arrow keys move between images on the same page.
2. **Web-optimised images:** each image is resized to at most 2000px wide and saved as WebP, plus a JPEG/PNG fallback at the same size, served with `<picture>`. Images use `loading="lazy"` (except the hero) and explicit `width`/`height` attributes to prevent layout shift.
3. **Light YouTube embeds:** each video first shows its YouTube thumbnail with a play button, and the real `youtube-nocookie.com` iframe loads only on click. This keeps pages fast with 10 videos on one page.
4. **Previous/next project navigation** at the bottom of project pages.
5. **Footer** with About and contact info.
6. **Basic SEO:** a `<title>` and meta description on every page, plus Open Graph tags (title, description, image) so shared links show a preview.

## Videos: placeholder until uploaded

Each video block is defined in the HTML with a `data-youtube-id` attribute. Until Juha has uploaded a video, its block shows a neutral "Video coming soon" panel with the caption, and the page still works. When he sends the YouTube links, only the `data-youtube-id` values change.

Before the videos come down from Adobe, Juha matches each of the 20 videos to its original file. The implementation creates `docs/video-checklist.md`, listing each video by page, position and caption so he can tick them off as he uploads.

## Content migration

A one-off script in `tools/` reads the 5 project pages and the home page of the current site and:
1. Downloads every image at its largest served size into a temporary folder (not committed).
2. Records the text, captions and block order per page.

The images are then resized/converted into `assets/images/<slug>/` with predictable names (`01.webp`, `01.jpg`, …), and the HTML pages are written from the recorded content. The script exists only for the migration; the site does not depend on it.

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

- A CMS or admin interface; content is edited directly in HTML.
- A contact form (email link only).
- Analytics.
- A custom domain (can be added later).
- Redirects from the old `myportfolio.com` URLs (Adobe controls that domain).
