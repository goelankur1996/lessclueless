# Less Clueless

Static site for [lessclueless.me](https://lessclueless.me). No framework, no build
dependencies beyond Python 3. Hosted on GitHub Pages.

## Structure

```
.
├── index.html                 # Home / writing list  (GENERATED — do not hand-edit)
├── 404.html
├── CNAME                      # Custom domain for GitHub Pages
├── posts/                     # One .html per post    (GENERATED — do not hand-edit)
├── assets/
│   ├── css/style.css          # All styling
│   ├── js/                    # (empty for now — for future interactivity)
│   └── img/
│       ├── favicon.svg
│       └── <slug>/...         # Images per post (copied from content/raw by build)
├── content/
│   ├── posts.json             # SOURCE OF TRUTH: metadata + post order
│   └── raw/                   # Raw Notion HTML exports + their image folders
└── scripts/
    └── build.py               # Regenerates index.html + posts/ from content/
```

`index.html` and everything in `posts/` are generated. Edit content via
`content/posts.json` and the raw exports, then rebuild.

## Add a new post

1. In Notion, export the page as **HTML** (`... → Export → HTML, include subpages off`).
2. Unzip it. Copy the post's `.html` file **and** its image folder into `content/raw/`.
3. Add an entry to the top of the `posts` array in `content/posts.json`:

   ```json
   {
     "slug": "my-new-post",
     "title": "My new post title",
     "description": "One-line summary shown on the home page.",
     "date": "2026-07-20",
     "tags": ["robotics"],
     "source": "My new post title <hash>.html"
   }
   ```

   `source` must match the exact `.html` filename you copied in (Notion appends a
   hash). `slug` becomes the URL: `/posts/my-new-post.html`.

4. Rebuild and preview:

   ```bash
   python3 scripts/build.py
   python3 -m http.server 8000    # open http://localhost:8000
   ```

5. Commit and push. GitHub Pages redeploys automatically.

   ```bash
   git add -A && git commit -m "Add post: my new post title" && git push
   ```

## Notes

- Posts are shown on the home page in the order they appear in `posts.json`.
- Videos: local `.mp4` attachments from Notion become inline `<video>` players.
- Dark mode is automatic (follows the reader's OS setting).
- To change site-wide text (tagline, socials, footer), edit the `site` block in
  `content/posts.json` and rebuild.
