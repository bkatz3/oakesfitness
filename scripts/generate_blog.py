#!/usr/bin/env python3
import os
import re
import sys
import time
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
import anthropic


@dataclass
class Topic:
    number: int
    title: str
    status: str  # "🟢" or "✅"
    tier: str    # "T1" or "T2"
    category: str
    line_index: int


def log(level: str, msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {level.upper()}: {msg}")


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text


def is_relative(p: str) -> bool:
    return not (p.startswith("/") or re.match(r"^[A-Za-z]:\\", p))


def load_topic_file(path: Path):
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)

    topics = {}
    topic_order = []

    current_tier = None
    current_category = ""

    for i, line in enumerate(lines):
        line_stripped = line.strip()

        if line_stripped.startswith("## Tier 1"):
            current_tier = "T1"
            continue
        if line_stripped.startswith("## Tier 2"):
            current_tier = "T2"
            continue
        if line_stripped.startswith("### "):
            current_category = line_stripped[4:].strip()
            continue

        m = re.match(r"^(\d+)\.\s+(🟢|✅)\s+(.*)$", line_stripped)
        if m:
            number = int(m.group(1))
            status = m.group(2)
            title = m.group(3).strip()
            if status == "✅":
                title = re.sub(r"^Written\s*\([^)]*\)\s+", "", title)
            topic = Topic(
                number=number,
                title=title,
                status=status,
                tier=current_tier or "",
                category=current_category,
                line_index=i,
            )
            topics[number] = topic
            topic_order.append(number)

    return content, lines, topics, topic_order


def parse_suggested_order(content: str):
    lines = content.splitlines()
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("## Suggested Publishing Order"):
            start_idx = i
            break
    if start_idx is None:
        return []

    ordered = []
    for line in lines[start_idx + 1:]:
        if not line.strip().startswith("|"):
            if ordered:
                break
            continue
        if "---" in line:
            continue
        parts = [p.strip() for p in line.strip().strip("|").split("|")]
        if len(parts) < 4:
            continue
        try:
            order_num = int(parts[0])
            topic_num = int(parts[1])
            tier = parts[2]
            topic_title = parts[3]
        except ValueError:
            continue
        ordered.append({
            "order": order_num,
            "number": topic_num,
            "tier": tier,
            "title": topic_title,
        })

    ordered.sort(key=lambda x: x["order"])
    return ordered


def select_next_topic(content: str, topics: dict, topic_order: list):
    suggested = parse_suggested_order(content)
    for row in suggested:
        num = row["number"]
        topic = topics.get(num)
        if topic and topic.status == "🟢":
            if topic.tier == "" and row.get("tier"):
                topic.tier = row["tier"]
            return topic

    for num in topic_order:
        topic = topics.get(num)
        if topic and topic.status == "🟢":
            return topic

    return None


def build_prompt(topic: Topic, skill_text: str, internal_links: list, existing_posts: list):
    links_text = ", ".join(internal_links) if internal_links else ""
    existing_text = ""
    if existing_posts:
        existing_text = "\n\nExisting posts for internal linking (title — slug):\n" + "\n".join(
            [f"- {p['title']} — {p['slug']}" for p in existing_posts]
        )

    user_msg = f"""Write the next blog post for oakesfitness.com.

Topic: {topic.title}
Tier: {topic.tier}
Category: {topic.category}
Topic Number: {topic.number}

Follow the deliverable format exactly as specified in your instructions.
Include the angle statement, meta description, keywords, full post body,
key takeaways, and NAP footer.

For research citations: Only include PubMed/NIH/peer-reviewed citations
you are confident are real. If you're unsure about a citation, flag it
with [VERIFY] so I can check it before publishing.

Internal links: Use the homepage and contact page for now. Targets: {links_text}.{existing_text}
"""

    return skill_text, user_msg


def parse_model_output(output: str):
    meta_desc = None
    primary_kw = None
    secondary_kws = []
    title = None
    angle_block = None

    m = re.search(r"\*\*Meta Description:\*\*\s*(.+)", output, flags=re.IGNORECASE)
    if m:
        meta_desc = m.group(1).strip().strip("[]")

    m = re.search(r"\*\*Primary Keyword:\*\*\s*(.+)", output, flags=re.IGNORECASE)
    if m:
        primary_kw = m.group(1).strip().strip("[]")

    m = re.search(r"\*\*Secondary Keywords:\*\*\s*(.+)", output, flags=re.IGNORECASE)
    if m:
        secondary_kws = [k.strip().strip('"') for k in m.group(1).split(",") if k.strip()]

    m = re.search(r"^#\s+(.+)$", output, flags=re.MULTILINE)
    if m:
        title = m.group(1).strip()

    angle_match = re.search(
        r"\*\*Angle Statement:\*\*\s*(.*?)\n---\n",
        output,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if angle_match:
        angle_block = angle_match.group(0).strip()

    return meta_desc, primary_kw, secondary_kws, title, angle_block


def strip_angle_statement(output: str) -> str:
    return re.sub(
        r"\*\*Angle Statement:\*\*.*?\n---\n",
        "",
        output,
        flags=re.DOTALL | re.IGNORECASE,
    ).strip()


def extract_public_body(output: str) -> str:
    stripped = strip_angle_statement(output)
    lines = stripped.splitlines()
    start_idx = None
    for i, line in enumerate(lines):
        if line.startswith("# "):
            start_idx = i
            break
    if start_idx is None:
        return stripped.strip()
    return "\n".join(lines[start_idx:]).strip()


def scan_existing_posts(blog_dir: Path):
    posts = []
    if not blog_dir.exists():
        return posts

    for path in sorted(blog_dir.glob("*.md")):
        title = None
        try:
            text = path.read_text(encoding="utf-8")
            for line in text.splitlines():
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip().strip('"')
                    break
        except Exception:
            continue
        if title:
            posts.append({"title": title, "slug": path.stem})

    return posts


def run_cmd(cmd, cwd: Path, check=True):
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr.strip()}")
    return result


def update_llms_file(llms_path: Path, title: str, slug: str) -> bool:
    if not llms_path.exists():
        log("warning", f"llms.txt not found at {llms_path}; skipping update.")
        return False

    url = f"https://oakesfitness.com/blog/{slug}"
    entry = f"- [{title}]({url})"

    text = llms_path.read_text(encoding="utf-8")
    if entry in text or url in text:
        log("info", "llms.txt already contains this blog post. Skipping update.")
        return False

    lines = text.splitlines()
    insert_idx = None
    for i, line in enumerate(lines):
        if line.strip() == "## Blog Posts":
            insert_idx = i + 1
            break

    if insert_idx is None:
        if lines and lines[-1].strip() != "":
            lines.append("")
        lines.append("## Blog Posts")
        lines.append("")
        lines.append(entry)
    else:
        if insert_idx < len(lines) and lines[insert_idx].strip() == "":
            insert_idx += 1
        end_idx = insert_idx
        while end_idx < len(lines) and not lines[end_idx].startswith("## "):
            end_idx += 1
        lines.insert(insert_idx, entry)

    llms_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    log("info", f"Updated {llms_path} with new blog post.")
    return True


def main():
    load_dotenv()

    repo_root = Path(__file__).resolve().parents[1]

    model = os.getenv("MODEL", "claude-sonnet-4-20250514")
    gh_repo = os.getenv("GH_REPO", "").strip()
    blog_output_dir = os.getenv("BLOG_OUTPUT_DIR", "content/blog")
    topic_file = os.getenv("TOPIC_FILE", "scripts/TOPIC_IDEAS.md")
    skill_file = os.getenv("SKILL_FILE", "scripts/oakesfitness_blog_skill.md")
    dry_run = os.getenv("DRY_RUN", "0") == "1"
    allow_dirty_tree = os.getenv("ALLOW_DIRTY_TREE", "0") == "1"

    if is_relative(blog_output_dir):
        blog_output_dir = str(repo_root / blog_output_dir)
    if is_relative(topic_file):
        topic_file = str(repo_root / topic_file)
    if is_relative(skill_file):
        skill_file = str(repo_root / skill_file)

    blog_dir = Path(blog_output_dir)
    topic_path = Path(topic_file)
    skill_path = Path(skill_file)

    dirty_tree = False
    if not dry_run:
        try:
            status = run_cmd(["git", "status", "--porcelain"], cwd=repo_root)
            if status.stdout.strip():
                dirty_tree = True
                if allow_dirty_tree:
                    log("warning", "Git working tree is dirty. Proceeding because ALLOW_DIRTY_TREE=1.")
                else:
                    log("error", "Git working tree is dirty. Commit or stash changes and retry.")
                    sys.exit(1)
        except Exception as e:
            log("error", f"Failed to check git status: {e}")
            sys.exit(1)

    if not topic_path.exists():
        log("error", f"TOPIC_IDEAS.md not found at {topic_path}")
        sys.exit(1)
    if not skill_path.exists():
        log("error", f"Skill file not found at {skill_path}")
        sys.exit(1)

    content, lines, topics, topic_order = load_topic_file(topic_path)
    topic = select_next_topic(content, topics, topic_order)
    if not topic:
        log("info", "No unwritten topics found. Exiting.")
        sys.exit(0)

    log("info", f"Selected topic #{topic.number}: {topic.title} ({topic.tier}, {topic.category})")

    skill_text = skill_path.read_text(encoding="utf-8")
    internal_links = ["index.html", "contact.html"]
    existing_posts = scan_existing_posts(blog_dir)

    system_prompt, user_prompt = build_prompt(topic, skill_text, internal_links, existing_posts)

    if dry_run:
        log("info", "DRY_RUN enabled. Skipping API call and git operations.")
        sys.exit(0)

    client = anthropic.Anthropic()

    log("info", f"Calling Anthropic model {model}...")
    try:
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as e:
        log("error", f"Anthropic API error: {e}")
        log("info", "Retrying once in 30 seconds...")
        time.sleep(30)
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

    output_text = ""
    if hasattr(message, "content") and message.content:
        if isinstance(message.content, list):
            output_text = "".join([c.text for c in message.content if hasattr(c, "text")])
        else:
            output_text = str(message.content)

    if not output_text.strip():
        log("error", "Empty model response.")
        sys.exit(1)

    meta_desc, primary_kw, secondary_kws, title, angle_block = parse_model_output(output_text)

    if not title or not meta_desc or not primary_kw:
        debug_path = repo_root / "scripts" / "last_model_output.txt"
        debug_path.write_text(output_text, encoding="utf-8")
        log("error", f"Failed to parse model output. Saved raw output to {debug_path}")
        sys.exit(1)

    today = date.today().isoformat()
    slug = slugify(title)
    filename = f"{today}-{slug}.md"

    blog_dir.mkdir(parents=True, exist_ok=True)
    out_path = blog_dir / filename

    frontmatter = [
        "---",
        f"title: \"{title}\"",
        f"date: {today}",
        "author: \"The Oakes Fitness Team\"",
        f"tier: {topic.tier.replace('T', '')}",
        f"category: \"{topic.category}\"",
        "draft: true",
        "---",
    ]

    def write_outputs():
        public_body = extract_public_body(output_text)
        out_text = "\n".join(frontmatter) + "\n\n" + public_body + "\n"
        out_path.write_text(out_text, encoding="utf-8")
        log("info", f"Wrote post to {out_path}")

        # Update TOPIC_IDEAS.md
        new_line = f"{topic.number}. ✅ Written ({today}) {topic.title}\n"
        lines[topic.line_index] = new_line
        topic_path.write_text("".join(lines), encoding="utf-8")
        log("info", f"Updated {topic_path} for topic #{topic.number}")

        llms_path = repo_root / "llms.txt"
        llms_updated = update_llms_file(llms_path, title, slug)
        return llms_path, llms_updated

    # Git + PR automation
    git_automation = True
    if dirty_tree and allow_dirty_tree:
        log("info", "Skipping git automation because working tree is dirty.")
        git_automation = False

    try:
        if not git_automation:
            write_outputs()
            return

        branch_name = f"blog/{today}-{slug}"

        current_branch = run_cmd(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo_root,
        ).stdout.strip()
        if current_branch != "main":
            run_cmd(["git", "checkout", "main"], cwd=repo_root)
        run_cmd(["git", "pull", "origin", "main"], cwd=repo_root)
        run_cmd(["git", "checkout", "-b", branch_name], cwd=repo_root)

        llms_path, llms_updated = write_outputs()

        run_cmd(["git", "add", str(out_path)], cwd=repo_root)
        run_cmd(["git", "add", str(topic_path)], cwd=repo_root)
        if llms_updated:
            run_cmd(["git", "add", str(llms_path)], cwd=repo_root)
        run_cmd(["git", "commit", "-m", f"blog: Add post - {title}"], cwd=repo_root)
        run_cmd(["git", "push", "origin", branch_name], cwd=repo_root)

        if gh_repo and shutil.which("gh"):
            pr_body = (
                "Auto-generated blog post for review.\n\n"
                f"Topic: {title}\n"
                f"Tier: {topic.tier}\n"
                f"Category: {topic.category}\n\n"
                "Please review before merging."
            )
            run_cmd([
                "gh", "pr", "create",
                "--repo", gh_repo,
                "--title", f"Blog Post: {title}",
                "--body", pr_body,
                "--draft",
            ], cwd=repo_root)
            log("info", "Created draft PR via gh.")

            if angle_block:
                run_cmd([
                    "gh", "pr", "comment",
                    "--repo", gh_repo,
                    "--body", angle_block,
                ], cwd=repo_root)
                log("info", "Posted angle statement as PR comment.")
        else:
            log("info", "Skipping PR creation (GH_REPO not set or gh not available).")

    except Exception as e:
        log("error", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
