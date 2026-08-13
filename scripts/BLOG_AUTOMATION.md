# Oakes Fitness — Autonomous Daily Blog Post (Cloud Agent Spec)

This file is the complete, self-contained instruction set for the scheduled cloud agent that writes one blog post per day and opens a draft PR. It runs UNATTENDED: no questions, no pauses, no plans awaiting approval. Execute end-to-end or abort with a one-line reason.

## Hard Rules (Non-Negotiable)

- NEVER push to `main`. NEVER merge a PR.
- ALWAYS open the PR as a draft.
- One run = one post = one PR. If today's branch already exists on origin, abort.
- Branch format: `blog/YYYY-MM-DD-slug`
- Never fabricate a citation. If a claim can't be sourced to peer-reviewed research, frame it as practitioner experience.

## Step 1: Preflight

1. Confirm you are on `main` with a clean tree.
2. Run `git ls-remote --heads origin 'blog/YYYY-MM-DD-*'` with today's date. If any branch matches, abort: `ABORT (preflight): today's post branch already exists.`

## Step 2: Pick a Topic

Read `scripts/TOPIC_IDEAS.md`. Pick the first line marked 🟢, reading top to bottom. Note its category (the nearest `###` heading above it, stripping any "(Batch 2)" suffix).

If there are no 🟢 lines, abort: `ABORT (no topics): TOPIC_IDEAS.md has no 🟢 entries. Refill the queue.`

Dupe check: compare the topic against every ✅ line and every file in `blog/`. If it overlaps an existing post, mark it `⏸ Skipped (duplicate)` and take the next 🟢. After 3 skips, abort.

## Step 3: Define the Angle (Before Writing)

Write down, for the PR description:
- What misconception, mistake, or confusion is being corrected?
- Why is this specifically different for adults over 50?
- What will the reader learn that a generic fitness blog wouldn't give them?

## Step 4: Write the Post

File: `blog/YYYY-MM-DD-slug.md` (slug = kebab-case title, drop filler words)

```markdown
---
title: "{title}"
date: YYYY-MM-DD
author: "The Oakes Fitness Team"
category: "{category}"
---

# {H1 = title}

*By The Oakes Fitness Team*

[body]

## Key Takeaways

- [3-5 bullets]

---

**Oakes Fitness** | Westford, MA | oakesfitness.com
*Serving Westford, Chelmsford, Littleton, Groton, Acton, and surrounding communities.*
```

### Audience

Adults over 50 in Westford, MA and surrounding towns (average client age 55): people returning to fitness after years away or after injury, busy 50s/60s professionals, recently retired adults, recreational athletes (golf, tennis, pickleball, running), and anyone navigating menopause, low testosterone, slower recovery, or joint issues. Every post must address at least one 50+ reality: slower connective tissue recovery, hormonal shifts, joint degeneration, sleep changes, time constraints, or psychological barriers from past injury or gym intimidation.

### Voice

Experienced personal trainer who specializes in adults over 50. Direct, confident, warm but not cheesy. Never frame aging as decline; frame it as requiring smarter strategy. Be specific about WHY things change after 50 (hormones, connective tissue, recovery capacity). Always pair "what changes" with "what to do about it." Impersonal editorial voice; "we" only when speaking as Oakes Fitness. Never first person "I".

### Structure

1. Hook first: misconception challenge, surprising data, or relatable 50+ problem. No throat-clearing.
2. 2-3 H2s phrased as exact questions people type into Google or ChatGPT. Don't force "after 50" into every H2.
3. Inverted pyramid: lead every section with the direct answer, then elaborate.
4. Concrete numbers, no vague claims. Active voice. No paragraph over 3-4 sentences.
5. At least one comparison table or bullet/numbered list.
6. Internal links: at least 1 existing post from `blog/` (URL form `https://oakesfitness.com/blog/{filename}.html`) + 1 service page (`https://oakesfitness.com/body-audit.html` or `https://oakesfitness.com/contact.html`).
7. H1 must read like a real search query. Primary keyword in title, first 100 words, and at least one H2.
8. Key Takeaways: 3-5 standalone sentences, at least one containing a concrete number.

### Tiers

- Tier 2 (default, any non-local topic): 650-800 words. Max one subtle Oakes Fitness mention, earned, e.g. the free 360° Body Audit sentence. No forced geography.
- Tier 1 (topics under "Local / Commercial"): 600-750 words. "Westford, MA" ~2 times naturally, mention 1-2 surrounding towns, and include: one diagnostic question about a common mistake, one consequence of doing it wrong, one low-friction CTA (free 360° Body Audit or visit).

### Evidence Standards (Strict)

- Cite PubMed, NIH, JAMA, or peer-reviewed journals only. No blogs, no media summaries, no aggregators.
- Verify every link resolves and the page matches the claim before including it.
- When citing a study: include population age, sample size, duration, and the specific measured outcome.
- Nutrition/physiology claims:
  - Calorie multipliers are "rough coaching heuristics," never physiology rules; note that daily movement outside workouts drives the estimate.
  - Protein baseline for a general 50+ audience: 0.5-0.7 g/lb. Frame higher intakes as for very active people or those in a deficit.
  - No absolute "X causes Y" mechanism claims; use risk framing ("increases the risk of muscle loss and poor recovery, especially in older adults").
  - Say "anabolic resistance increases with age" (a bigger stimulus is required), not "muscle protein synthesis becomes less efficient."

### Banned (Voice Pass)

Em dashes. "Dive into," "unlock," "harness," "leverage," "game-changer," "at the end of the day," "in today's world," "whether you're a beginner or advanced," "look no further," "embark," "realm," "delve," "crucial," "robust," "comprehensive," "arguably," "in conclusion," "it's worth noting," "it's important to note," "transform your body/life," "start your journey," "it's never too late," "age is just a number," "anti-aging," "silver/golden years." Nothing that pattern-matches to AI-generated text.

## Step 5: Self-Review (Up to 3 Loops)

Each loop: verify every citation link resolves and matches its claim; check markdown formatting and complete frontmatter; check banned list and em dashes; check word count for the tier; check Key Takeaways standard; check internal links point to files that exist in `blog/`. Fix and loop until clean. If issues remain after 3 loops, note them in the PR body as `[UNRESOLVED]` and continue.

## Step 6: Build and Update Tracking Files

1. Create the branch: `git checkout -b blog/YYYY-MM-DD-slug`
2. Run `python3 scripts/build_blog.py` from the repo root. If it fails, abort: `ABORT (build): {error}`.
3. Update `scripts/TOPIC_IDEAS.md`: change the topic's `🟢` to `✅ Written (YYYY-MM-DD) {title}` and add the same line to `## Already Written`.
4. Update `llms.txt`: add `- [{title}](https://oakesfitness.com/blog/{slug})` at the top of `## Blog Posts`.

## Step 7: Commit, Push, Draft PR

1. `git add blog/{slug}.md scripts/TOPIC_IDEAS.md llms.txt sitemap.xml`
2. Commit: `blog: Add post - {title}`
3. Push the branch, then open a DRAFT PR titled `Blog Post: {title}` with body:

```
Tier: {1 or 2}
Category: {category}
Angle: {from Step 3}
Meta Description: {under 160 characters}
Primary Keyword: {keyword}
Secondary Keywords: {kw1}, {kw2}, {kw3}
Source: TOPIC_IDEAS.md (scheduled run)

Auto-generated. Please review before merging.
```

## Step 8: Stop

Report the PR URL and stop. Do not merge. Do not push anything else.
