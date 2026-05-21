"""
Enriches repos with commit velocity, fork ratio, and full metadata from GitHub API.
"""
from __future__ import annotations
import time
import requests
from config import GITHUB_TOKEN

BASE = "https://api.github.com"

def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "AIGithubPulse/1.0"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


def enrich_repo(repo: dict) -> dict:
    """Fetch full metadata + commit activity for one repo."""
    full_name = repo.get("full_name", "")
    if not full_name:
        return repo

    # Full repo metadata (stars, forks, topics, license, etc.)
    try:
        r = requests.get(f"{BASE}/repos/{full_name}", headers=_headers(), timeout=15)
        if r.status_code == 404:
            repo["not_found"] = True
            return repo
        r.raise_for_status()
        data = r.json()

        repo["stars"] = data.get("stargazers_count", repo.get("stars", 0))
        repo["forks"] = data.get("forks_count", repo.get("forks", 0))
        repo["open_issues"] = data.get("open_issues_count", 0)
        repo["watchers"] = data.get("subscribers_count", 0)
        repo["topics"] = data.get("topics", repo.get("topics", []))
        repo["description"] = data.get("description") or repo.get("description", "")
        repo["language"] = data.get("language") or repo.get("language", "")
        repo["is_archived"] = data.get("archived", False)
        repo["is_fork"] = data.get("fork", False)
        repo["pushed_at"] = data.get("pushed_at", "")
        repo["created_at"] = data.get("created_at", "")
        repo["license"] = (data.get("license") or {}).get("spdx_id", "")
        repo["has_sponsors"] = bool(data.get("has_sponsorships_enabled"))
    except Exception:
        pass

    # Commit activity (weekly commits for past year)
    try:
        r = requests.get(f"{BASE}/repos/{full_name}/stats/commit_activity", headers=_headers(), timeout=15)
        if r.status_code == 200 and r.json():
            weeks = r.json()
            last_4_weeks = sum(w.get("total", 0) for w in weeks[-4:])
            repo["commits_last_4w"] = last_4_weeks
        else:
            repo["commits_last_4w"] = 0
        time.sleep(0.3)
    except Exception:
        repo["commits_last_4w"] = 0

    return repo


def enrich_batch(repos: list[dict], max_enrich: int = 30) -> list[dict]:
    """Enrich top N repos (sorted by initial score to save API calls)."""
    to_enrich = repos[:max_enrich]
    rest = repos[max_enrich:]

    enriched = []
    for repo in to_enrich:
        enriched.append(enrich_repo(repo))
        time.sleep(0.5)

    return enriched + rest
