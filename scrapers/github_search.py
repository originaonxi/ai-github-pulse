"""
GitHub Search API — finds AI/agent repos with 1k+ stars sorted by recent activity.
Covers repos not on trending page but still highly relevant.
"""
from __future__ import annotations
import time
import requests
from datetime import date, timedelta
from config import GITHUB_TOKEN, MIN_STARS

BASE = "https://api.github.com"

def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "AIGithubPulse/1.0"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h

# Search queries targeting our exact topic set
SEARCH_QUERIES = [
    "topic:agent stars:>1000 pushed:>2025-01-01",
    "topic:llm stars:>1000 pushed:>2025-01-01",
    "topic:mcp stars:>1000 pushed:>2025-01-01",
    "topic:agi stars:>1000 pushed:>2025-01-01",
    "topic:claude stars:>1000 pushed:>2025-01-01",
    "topic:memory stars:>1000 topic:ai",
    "ai agent cli stars:>2000 pushed:>2025-01-01",
    "llm terminal stars:>1000 pushed:>2025-01-01",
]


def search_repos(query: str, per_page: int = 20) -> list[dict]:
    try:
        r = requests.get(
            f"{BASE}/search/repositories",
            headers=_headers(),
            params={"q": query, "sort": "updated", "order": "desc", "per_page": per_page},
            timeout=20,
        )
        if r.status_code == 403:
            print(f"  GitHub Search rate limit hit")
            return []
        r.raise_for_status()
        items = r.json().get("items", [])
        return [_normalize(item) for item in items]
    except Exception as e:
        print(f"  GitHub Search error: {e}")
        return []


def _normalize(item: dict) -> dict:
    owner = item.get("owner", {}).get("login", "")
    topics = item.get("topics", [])
    return {
        "full_name": item.get("full_name", ""),
        "owner": owner,
        "repo": item.get("name", ""),
        "description": item.get("description") or "",
        "stars": item.get("stargazers_count", 0),
        "forks": item.get("forks_count", 0),
        "open_issues": item.get("open_issues_count", 0),
        "language": item.get("language") or "",
        "topics": topics,
        "pushed_at": item.get("pushed_at", ""),
        "created_at": item.get("created_at", ""),
        "is_fork": item.get("fork", False),
        "is_archived": item.get("archived", False),
        "url": item.get("html_url", ""),
        "homepage": item.get("homepage") or "",
        "source": "github_search",
        "scraped_date": date.today().isoformat(),
        "stars_today": 0,  # not available from search, enriched later
    }


def scrape_all_searches() -> list[dict]:
    seen = set()
    all_repos = []
    for query in SEARCH_QUERIES:
        repos = search_repos(query, per_page=15)
        for r in repos:
            fn = r["full_name"]
            if fn and fn not in seen:
                seen.add(fn)
                all_repos.append(r)
        time.sleep(1.5)  # respect rate limits
    print(f"  GitHub Search: {len(all_repos)} repos found")
    return all_repos
