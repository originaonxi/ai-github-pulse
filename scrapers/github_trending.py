"""
Scrapes github.com/trending for today's trending repos.
Key signal: stars_today — repos gaining the most stars right now.
No API key needed.
"""
from __future__ import annotations
import re
import requests
from datetime import date

BASE = "https://github.com"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AIGithubPulse/1.0"}

LANGUAGES = ["", "python", "typescript", "javascript", "rust", "go"]


def scrape_trending(language: str = "", since: str = "daily") -> list[dict]:
    url = f"{BASE}/trending/{language}?since={since}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        html = r.text
        return _parse_trending_html(html)
    except Exception as e:
        print(f"  Trending scrape error ({language or 'all'}): {e}")
        return []


def _parse_trending_html(html: str) -> list[dict]:
    repos = []
    # Each trending repo is in an <article> block
    articles = re.findall(r'<article[^>]*class="[^"]*Box-row[^"]*"[^>]*>(.*?)</article>', html, re.DOTALL)

    for article in articles:
        # Full name: owner/repo
        name_match = re.search(r'href="/([^/"]+/[^/"]+)"[^>]*>\s*<span[^>]*>[^<]*</span>[^<]*<span[^>]*>([^<]+)</span>', article)
        if not name_match:
            name_match = re.search(r'href="/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)"', article)
        if not name_match:
            continue
        full_name = name_match.group(1).strip()
        if full_name.count("/") != 1:
            continue

        # Description
        desc_match = re.search(r'<p[^>]*class="[^"]*col-9[^"]*"[^>]*>(.*?)</p>', article, re.DOTALL)
        description = ""
        if desc_match:
            description = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()

        # Stars today
        stars_today = 0
        today_match = re.search(r'([\d,]+)\s+stars?\s+today', article, re.IGNORECASE)
        if today_match:
            stars_today = int(today_match.group(1).replace(",", ""))

        # Language
        lang_match = re.search(r'itemprop="programmingLanguage"[^>]*>([^<]+)<', article)
        language = lang_match.group(1).strip() if lang_match else ""

        # Topics from article (sometimes present)
        topics = re.findall(r'href="/topics/([^"]+)"', article)

        owner, repo = full_name.split("/", 1)
        repos.append({
            "full_name": full_name,
            "owner": owner,
            "repo": repo,
            "description": description,
            "stars_today": stars_today,
            "language": language,
            "topics": topics,
            "url": f"https://github.com/{full_name}",
            "source": "github_trending",
            "scraped_date": date.today().isoformat(),
        })

    return repos


def scrape_all_trending() -> list[dict]:
    """Scrape trending across all languages + top AI languages."""
    seen = set()
    all_repos = []

    for lang in LANGUAGES:
        repos = scrape_trending(language=lang, since="daily")
        for r in repos:
            if r["full_name"] not in seen:
                seen.add(r["full_name"])
                all_repos.append(r)

    print(f"  GitHub Trending: {len(all_repos)} repos found")
    return all_repos
