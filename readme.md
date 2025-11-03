# Creating a New Post

Use the existing English (`en/`) and Portuguese (`pt/`) structures to add new articles. Each post needs a Markdown file, optional images, and a manifest entry.

## 1. Choose the language folder

- English posts go in `en/posts/`
- Portuguese posts go in `pt/posts/`
- Name the file `YYYY-MM-DD-slug.md` (e.g. `2025-11-12-my-new-piece.md`)

## 2. Create the Markdown file

Each post starts with front matter that drives the listing and the post page.

```markdown
---
title: "My Post Title"
date: 2025-11-12T18:00:00+00:00
categories: ["Categoria 1", "Categoria 2"]
source: https://example.com/original-post   # optional
excerpt: A one-sentence teaser for the article listing.
---
Opening paragraph…

![](static/articles/my-new-piece/image-01.jpg)

More content here…
```

- `title`, `date`, `categories`, and `excerpt` are required.
- `source` is optional but useful when mirroring an external article.
- Write the body in Markdown. Leave blank lines between paragraphs.

## 3. Add supporting assets (optional)

Images live under `static/articles/` inside the language folder. Use a slug-matching directory to keep files organised.

```
en/static/articles/my-new-piece/image-01.jpg
pt/static/articles/my-new-piece/image-01.jpg
```

Reference them from Markdown as:

```markdown
![](static/articles/my-new-piece/image-01.jpg)
```

## 4. Update the manifest

Each language has a post manifest (`en/posts/index.json` or `pt/posts/index.json`). Add an entry near the top so the article appears in the listing.

```json
{
  "title": "My Post Title",
  "date": "2025-11-12T18:00:00+00:00",
  "categories": ["Categoria 1", "Categoria 2"],
  "path": "2025-11-12-my-new-piece.md",
  "source": "https://example.com/original-post",
  "excerpt": "A one-sentence teaser for the article listing."
}
```

- Keep the array sorted newest first.
- Remove or leave out the `source` field if you do not have one.

## 5. Preview locally

Run your preferred static server in the project root (example: `python3 -m http.server`) and navigate to:

- `/en/index.html` (or `/pt/index.html`) to confirm the card appears.
- `/en/post.html?post=2025-11-12-my-new-piece.md` to review the full article page.

Repeat the same steps in the other language folder if you publish a translated version.
