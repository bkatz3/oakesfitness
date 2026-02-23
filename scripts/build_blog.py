#!/usr/bin/env python3
"""Build static HTML pages for blog posts and update blog.html listing.

Run from the repo root:
    python scripts/build_blog.py
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Error: pyyaml is required. Run: pip install pyyaml")

CONTENT_DIR = Path("content/blog")
BLOG_DIR = Path("blog")
BLOG_HTML = Path("blog.html")

MONTHS = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body_text). Body excludes the frontmatter block."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            fm = yaml.safe_load(text[4:end]) or {}
            return fm, text[end + 5:].strip()
    return {}, text.strip()


def inline_md(text: str) -> str:
    """Convert inline Markdown (bold, italic, links) to HTML."""
    text = re.sub(r"\*\*\*(.*?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"(?<!\*)\*(?!\*)(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", text)
    return text


def md_to_html(text: str) -> str:
    """Convert a subset of Markdown to HTML (headings, paragraphs, lists, hr)."""
    lines = text.split("\n")
    out: list[str] = []
    para: list[str] = []
    in_ul = False

    def flush_para() -> None:
        nonlocal para
        if para:
            out.append(f"<p>{inline_md(' '.join(para))}</p>")
            para = []

    def close_ul() -> None:
        nonlocal in_ul
        if in_ul:
            out.append("</ul>")
            in_ul = False

    for line in lines:
        s = line.strip()

        if re.fullmatch(r"-{3,}|\*{3,}", s):
            flush_para(); close_ul()
            out.append("<hr>")
            continue

        m = re.match(r"^(#{1,6})\s+(.*)", s)
        if m:
            flush_para(); close_ul()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline_md(m.group(2))}</h{lvl}>")
            continue

        m = re.match(r"^[-*]\s+(.*)", s)
        if m:
            flush_para()
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline_md(m.group(1))}</li>")
            continue

        if not s:
            flush_para(); close_ul()
            continue

        close_ul()
        para.append(s)

    flush_para(); close_ul()
    return "\n".join(out)


def strip_artifacts(body: str) -> str:
    """Remove generate_blog.py metadata preamble and leading H1/byline."""
    # Find the article H1, discarding any preamble before it
    m = re.search(r"(?:^|\n)(# .+)", body)
    if m:
        body = body[m.start():].lstrip("\n")
    # Remove H1
    body = re.sub(r"^# .+\n", "", body).strip()
    # Remove leading byline e.g. *By The Oakes Fitness Team*
    body = re.sub(r"^\*By[^\n]*\*\n+", "", body).strip()
    return body


# ---------------------------------------------------------------------------
# Metadata helpers
# ---------------------------------------------------------------------------

def format_date(val) -> str:
    """Return 'Month D, YYYY' from a date object or YYYY-MM-DD string."""
    if hasattr(val, "month"):
        return f"{MONTHS[val.month]} {val.day}, {val.year}"
    try:
        y, mo, d = str(val).split("-")
        return f"{MONTHS[int(mo)]} {int(d)}, {y}"
    except Exception:
        return str(val)


def iso_date(val) -> str:
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val)[:10]


def extract_description(body_html: str, max_chars: int = 200) -> str:
    m = re.search(r"<p>(.*?)</p>", body_html, re.DOTALL)
    if m:
        text = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if len(text) > max_chars:
            text = text[:max_chars].rsplit(" ", 1)[0] + "..."
        return text
    return ""


# ---------------------------------------------------------------------------
# HTML templates
# ---------------------------------------------------------------------------

NAV = """\
    <nav class="nav" id="nav">
        <div class="nav-container">
            <div class="nav-logo">
                <a href="/" style="text-decoration: none; color: inherit;">
                    <span class="logo-text">OAKES<span class="logo-accent">FITNESS</span></span>
                </a>
            </div>
            <div class="nav-links">
                <a href="/" class="mobile-only">Home</a>
                <a href="/#about">About</a>
                <a href="/#services">Services</a>
                <a href="/contact">Contact</a>
                <div class="nav-phones">
                    <a href="tel:978-277-6300" class="phone-link">Westford: 978-277-6300</a>
                    <a href="tel:978-680-5069" class="phone-link">Concord: 978-680-5069</a>
                </div>
                <a href="/contact" class="cta-button">Get a Free Consultation</a>
            </div>
            <button class="nav-toggle" id="navToggle">
                <span></span>
                <span></span>
                <span></span>
            </button>
        </div>
    </nav>"""

FOOTER = """\
    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-brand">
                    <div class="footer-logo">
                        <span class="logo-text">OAKES<span class="logo-accent">FITNESS</span></span>
                    </div>
                    <p class="footer-tagline">Best Personal Training Gyms in Westford &amp; Concord</p>
                </div>
                <div class="footer-locations">
                    <div class="location">
                        <h4>Westford Studio</h4>
                        <p>334 Littleton Road<br>Westford, MA 01886</p>
                        <a href="tel:978-277-6300">978-277-6300</a>
                    </div>
                    <div class="location">
                        <h4>Concord Studio</h4>
                        <p>97a Thoreau Street<br>Concord, MA 01742</p>
                        <a href="tel:978-680-5069">978-680-5069</a>
                    </div>
                </div>
                <div class="footer-contact">
                    <h4>Get In Touch</h4>
                    <a href="mailto:oakesfitness1@gmail.com">oakesfitness1@gmail.com</a>
                    <a href="/blog">Blog</a>
                    <p class="footer-serving">Serving Concord, Westford, Bedford, Carlisle, Littleton, Acton &amp; surrounding communities</p>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2026 Oakes Fitness. All rights reserved.</p>
            </div>
        </div>
    </footer>"""


def post_page_html(*, title, date_str, iso, author, category, description, body_html, slug):
    cat_html = f'<span class="card-category">{category}</span>' if category else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Oakes Fitness</title>
    <meta name="description" content="{description}">
    <link rel="canonical" href="https://oakesfitness.com/blog/{slug}">

    <meta property="og:type" content="article">
    <meta property="og:url" content="https://oakesfitness.com/blog/{slug}">
    <meta property="og:title" content="{title} | Oakes Fitness">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="https://oakesfitness.com/images/oakes_logo.jpg">

    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="https://oakesfitness.com/blog/{slug}">
    <meta property="twitter:title" content="{title} | Oakes Fitness">
    <meta property="twitter:description" content="{description}">
    <meta property="twitter:image" content="https://oakesfitness.com/images/oakes_logo.jpg">

    <link rel="icon" type="image/png" href="/images/oakes_logo_no_bg.png">
    <link rel="apple-touch-icon" href="/images/oakes_logo.jpg">
    <link rel="shortcut icon" href="/images/oakes_logo.jpg">
    <meta name="apple-mobile-web-app-title" content="Oakes Fitness">
    <meta name="application-name" content="Oakes Fitness">
    <meta name="theme-color" content="#2B8BFF">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/style.css">

    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": "{title}",
      "description": "{description}",
      "author": {{"@type": "Organization", "name": "{author}"}},
      "publisher": {{
        "@type": "Organization",
        "name": "Oakes Fitness",
        "logo": {{"@type": "ImageObject", "url": "https://oakesfitness.com/images/oakes_logo.jpg"}}
      }},
      "datePublished": "{iso}",
      "url": "https://oakesfitness.com/blog/{slug}"
    }}
    </script>
</head>
<body>
{NAV}

    <main>
    <article class="post-page">
        <div class="post-container">
            <a href="/blog" class="back-link">&#8592; Back to Blog</a>
            <header class="post-header">
                <div class="card-meta">
                    <span class="card-date">{date_str}</span>
                    {cat_html}
                </div>
                <h1>{title}</h1>
            </header>
            <div class="post-body">
{body_html}
            </div>
            <div class="post-footer">
                <a href="/blog" class="back-link">&#8592; Back to Blog</a>
            </div>
        </div>
    </article>
    </main>

{FOOTER}

    <script src="/script.js"></script>
</body>
</html>"""


def card_html(*, title, date_str, author, category, description, slug):
    return f"""\
                <a href="/blog/{slug}.html" class="update-card">
                    <div class="card-meta">
                        <span class="card-date">{date_str}</span>
                    </div>
                    <h2 class="card-title">{title}</h2>
                    <p class="card-summary">{description}</p>
                    <div class="card-author">{author}</div>
                </a>"""


# ---------------------------------------------------------------------------
# Listing page HTML + updaters
# ---------------------------------------------------------------------------

def listing_page_html(cards: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fitness Blog — News &amp; Updates | Oakes Fitness</title>
    <meta name="description" content="News and announcements from Oakes Fitness in Westford &amp; Concord, MA.">
    <link rel="canonical" href="https://oakesfitness.com/blog">

    <meta property="og:type" content="website">
    <meta property="og:url" content="https://oakesfitness.com/blog">
    <meta property="og:title" content="Fitness Blog — News &amp; Updates | Oakes Fitness">
    <meta property="og:description" content="News and announcements from Oakes Fitness in Westford &amp; Concord, MA.">
    <meta property="og:image" content="https://oakesfitness.com/images/oakes_logo.jpg">

    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:url" content="https://oakesfitness.com/blog">
    <meta property="twitter:title" content="Fitness Blog — News &amp; Updates | Oakes Fitness">
    <meta property="twitter:description" content="News and announcements from Oakes Fitness in Westford &amp; Concord, MA.">
    <meta property="twitter:image" content="https://oakesfitness.com/images/oakes_logo.jpg">

    <link rel="icon" type="image/png" href="/images/oakes_logo_no_bg.png">
    <link rel="apple-touch-icon" href="/images/oakes_logo.jpg">
    <link rel="shortcut icon" href="/images/oakes_logo.jpg">
    <meta name="apple-mobile-web-app-title" content="Oakes Fitness">
    <meta name="application-name" content="Oakes Fitness">
    <meta name="theme-color" content="#2B8BFF">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/style.css">

    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Home", "item": "https://oakesfitness.com/"}},
        {{"@type": "ListItem", "position": 2, "name": "Blog", "item": "https://oakesfitness.com/blog"}}
      ]
    }}
    </script>
</head>
<body>
{NAV}

    <main>
    <section class="blog-hero">
        <div class="container">
            <h1>Oakes Fitness <span class="hero-accent">Blog</span></h1>
            <p>News and announcements from Oakes Fitness</p>
        </div>
    </section>

    <section class="blog-list">
        <div class="container">
            <div class="blog-column">
{cards}
            </div>
        </div>
    </section>
    </main>

{FOOTER}

    <script src="/script.js"></script>
</body>
</html>"""


def update_blog_listing(cards: str) -> None:
    # Write blog/index.html (serves at /blog/ locally and /blog on Vercel)
    index_path = BLOG_DIR / "index.html"
    index_path.write_text(listing_page_html(cards), encoding="utf-8")
    print(f"  generated: {index_path}")

    # Also keep root blog.html in sync
    content = BLOG_HTML.read_text(encoding="utf-8")
    open_tag = '<div class="blog-column">'

    start = content.find(open_tag)
    if start == -1:
        raise RuntimeError("blog-column div not found in blog.html")

    inner_start = start + len(open_tag)

    # Find the *matching* closing </div> by tracking nesting depth.
    depth = 1
    pos = inner_start
    inner_end = -1
    while pos < len(content) and depth > 0:
        next_open = content.find("<div", pos)
        next_close = content.find("</div>", pos)
        if next_close == -1:
            break
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + 4
        else:
            depth -= 1
            if depth == 0:
                inner_end = next_close
            else:
                pos = next_close + 6
    if inner_end == -1:
        raise RuntimeError("Matching closing </div> for blog-column not found in blog.html")

    new_content = (
        content[:inner_start]
        + "\n"
        + cards
        + "\n            "
        + content[inner_end:]
    )
    BLOG_HTML.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not CONTENT_DIR.is_dir():
        sys.exit(f"Content directory not found: {CONTENT_DIR}")

    BLOG_DIR.mkdir(exist_ok=True)

    posts = []
    for md_file in sorted(CONTENT_DIR.glob("*.md"), reverse=True):
        raw = md_file.read_text(encoding="utf-8")
        fm, body_raw = parse_frontmatter(raw)

        if fm.get("draft", False):
            print(f"  skip (draft): {md_file.name}")
            continue

        slug = md_file.stem

        # Title from frontmatter or H1
        title = fm.get("title")
        if not title:
            m = re.search(r"^#\s+(.+)", body_raw, re.MULTILINE)
            title = m.group(1).strip() if m else slug

        # Strip preamble artifacts, H1, and byline from body
        body_clean = strip_artifacts(body_raw)
        body_html_content = md_to_html(body_clean)

        # Date from frontmatter or filename
        date_val = fm.get("date")
        if not date_val:
            m = re.match(r"(\d{4}-\d{2}-\d{2})", md_file.stem)
            date_val = m.group(1) if m else "2026-01-01"

        date_str = format_date(date_val)
        iso = iso_date(date_val)

        author = fm.get("author", "The Oakes Fitness Team")
        category = fm.get("category", "")
        description = fm.get("description", "") or extract_description(body_html_content)

        html = post_page_html(
            title=title,
            date_str=date_str,
            iso=iso,
            author=author,
            category=category,
            description=description,
            body_html=body_html_content,
            slug=slug,
        )
        out = BLOG_DIR / f"{slug}.html"
        out.write_text(html, encoding="utf-8")
        print(f"  generated: {out}")

        posts.append(dict(
            title=title,
            date_str=date_str,
            author=author,
            category=category,
            description=description,
            slug=slug,
        ))

    if not posts:
        print("No published posts found (all may have draft: true).")
        return

    cards = "\n".join(card_html(**p) for p in posts)
    update_blog_listing(cards)
    print(f"  updated:   {BLOG_HTML}")
    print(f"\nBuilt {len(posts)} post(s).")


if __name__ == "__main__":
    main()
