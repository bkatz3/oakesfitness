# Oakes Fitness Blog Automation

This repo includes a script that generates an Oakes Fitness blog post, writes it to `content/blog/`, updates `scripts/TOPIC_IDEAS.md`, and opens a draft PR.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY
```

## Run

```bash
python scripts/generate_blog.py
```

## Scheduling

### macOS (launchd)
Create `~/Library/LaunchAgents/com.oakesfitness.bloggen.plist` and load it with `launchctl`.

### Linux (cron)

```bash
0 6 * * * cd /path/to/repo && /path/to/python scripts/generate_blog.py >> /tmp/bloggen.log 2>&1
```

## Notes

- Posts are created as drafts with `draft: true` in frontmatter.
- PRs are created as drafts for human review.
- If a citation is uncertain, it is marked `[VERIFY]` in the output.
