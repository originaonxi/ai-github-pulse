"""
LLM story writer for AI GitHub Pulse.
Uses Requesty (Claude Sonnet) to write repo stories.
Format: Hook → What it does → Why engineers care → Signal
"""
from __future__ import annotations
import json, re
from openai import OpenAI
from config import REQUESTY_API_KEY, REQUESTY_BASE_URL, REQUESTY_MODEL, MAX_STORIES

_client = OpenAI(api_key=REQUESTY_API_KEY, base_url=REQUESTY_BASE_URL)


def _chat(system: str, user: str, max_tokens: int = 600) -> str:
    resp = _client.chat.completions.create(
        model=REQUESTY_MODEL,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    )
    return resp.choices[0].message.content.strip()


SELECTOR_SYSTEM = """You are the editor of "AI GitHub Pulse" — a daily newsletter for engineers who build with AI.
Your job: pick 1 to 5 GitHub repos that EVERY AI engineer needs to see today.

These repos are pre-scored by star velocity, topic match, org prestige, and commit momentum.
Your job is final editorial judgment.

Priority (in order):
1. Repos that represent a NEW category or approach — not just another LLM wrapper
2. Repos from known AI orgs (Anthropic, OpenAI, Meta, Google, Mistral, etc.)
3. Repos gaining massive traction RIGHT NOW (high stars today)
4. Tools that solve real pain points for AI builders (agents, memory, terminal, MCP)
5. One per category max — don't pick 3 agent frameworks

REJECT: awesome lists, tutorials, courses, boilerplate, forks of existing tools
CRITICAL: If only 1-2 repos are truly remarkable today, pick 1-2. Don't pad to 5."""


WRITER_SYSTEM = """You are the writer of "AI GitHub Pulse" — the sharpest daily GitHub newsletter for AI engineers.
Write like a senior engineer who just found something genuinely exciting and is texting a brilliant colleague.

Style rules:
- Open with the most surprising or exciting fact about this repo
- Be specific: name the architecture, the technique, the benchmark
- No hype words: never say "revolutionary", "game-changing", "groundbreaking"
- Show the star signal naturally — "It hit 3k stars in 48 hours" not "it's popular"
- End with one concrete reason why a builder should try it TODAY
- Max 200 words per repo"""


def select_top_repos(candidates: list[dict], qualified_count: int = 0) -> list[dict]:
    if not candidates:
        return []

    max_pick = min(MAX_STORIES, len(candidates))
    candidate_list = "\n".join([
        f"{i+1}. [{c.get('composite_score',0)}pts] {c.get('full_name','')} — {c.get('description','')[:80]}\n"
        f"   stars={c.get('stars',0):,} | today=+{c.get('stars_today',0)} | forks={c.get('forks',0):,} | "
        f"lang={c.get('language','')} | topics={','.join(c.get('topics',[])[:4])}\n"
        f"   score: topic={c.get('score_breakdown',{}).get('topic',0)} prestige={c.get('score_breakdown',{}).get('prestige',0)} "
        f"velocity={c.get('score_breakdown',{}).get('velocity',0)}"
        for i, c in enumerate(candidates)
    ])

    try:
        text = _chat(
            SELECTOR_SYSTEM,
            f"Today's pre-scored AI repos ({len(candidates)} from {qualified_count} qualified):\n\n{candidate_list}\n\n"
            f"Pick 1 to {max_pick} that every AI engineer MUST see today.\n"
            f"Return ONLY a JSON array of numbers: [2, 5, 1]",
            max_tokens=200,
        )
        m = re.search(r'\[[\d,\s]+\]', text)
        indices = json.loads(m.group() if m else text)
        selected = [candidates[i-1] for i in indices if 0 < i <= len(candidates)]
        return selected[:max_pick]
    except Exception as e:
        print(f"  Selector error: {e}, using top 3 by score")
        return candidates[:min(3, max_pick)]


def write_repo_story(repo: dict, number: int) -> dict:
    stars = repo.get("stars", 0)
    stars_today = repo.get("stars_today", 0)
    forks = repo.get("forks", 0)
    language = repo.get("language", "")
    topics = ", ".join(repo.get("topics", [])[:6])
    description = repo.get("description") or "No description"
    commits_4w = repo.get("commits_last_4w", 0)
    owner = repo.get("owner", "")
    breakdown = repo.get("score_breakdown", {})

    prompt = f"""Write story #{number} for "AI GitHub Pulse" about this GitHub repo.

Repo: {repo.get('full_name', '')}
Description: {description}
Stars: {stars:,} total{f', +{stars_today} today' if stars_today else ''}
Forks: {forks:,} | Language: {language} | Topics: {topics}
Commits last 4 weeks: {commits_4w}
URL: {repo.get('url', '')}

Write in this EXACT structure (use these exact headers):

**Hook** — One punchy sentence: the most surprising fact or the exact problem this solves.

**What it does** — 2-3 sentences: how it works, key technical approach, what makes it different from alternatives.

**Why you should care** — 2 sentences: specific use case for an AI engineer building agents/tools/LLMs today.

**The signal** — 1 sentence naturally mentioning the traction (stars, growth, org behind it).

Total: under 200 words. No bullet points. No hype adjectives."""

    try:
        content = _chat(WRITER_SYSTEM, prompt, max_tokens=500)
        return {
            "number": number,
            "full_name": repo.get("full_name", ""),
            "url": repo.get("url", "#"),
            "stars": stars,
            "stars_today": stars_today,
            "language": language,
            "owner": owner,
            "description": description,
            "content": content,
            "repo": repo,
            "score": repo.get("composite_score", 0),
        }
    except Exception as e:
        return {
            "number": number,
            "full_name": repo.get("full_name", ""),
            "url": repo.get("url", "#"),
            "content": f"*Story generation failed: {e}*",
            "repo": repo,
            "score": 0,
        }


def write_closing(stories: list[dict], total_scraped: int) -> str:
    names = [f"{s['number']}. {s['full_name']}" for s in stories]
    try:
        return _chat(
            "You are a sharp engineering newsletter editor. Be direct and specific.",
            f"Write a 2-sentence closing for today's AI GitHub Pulse.\n"
            f"We scanned {total_scraped} repos and chose {len(stories)}:\n"
            + "\n".join(names) +
            "\nExplain WHY these specifically — what signal made them stand out. "
            "No filler, no hype. Return only 2 sentences.",
            max_tokens=150,
        )
    except Exception:
        return f"Scanned {total_scraped} repos today. These {len(stories)} had the clearest signal — real traction, active development, and problems AI builders actually face."
