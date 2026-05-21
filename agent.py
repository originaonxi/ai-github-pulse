"""
AI GitHub Pulse — Daily GitHub trending repos newsletter.
Covers: AI, agents, LLMs, Claude, Codex, terminal, memory, AGI.
Minimum 1k stars. 1-5 repos/day. Only the remarkable ones.

Pipeline:
1. Scrape GitHub Trending (stars today signal)
2. GitHub Search API (topic-targeted repos)
3. Merge + enrich with commit velocity, fork ratio
4. Composite score (velocity + topic + prestige + momentum)
5. Claude selects 1-5 must-see repos
6. Claude writes stories
7. Send dark HTML email
"""
from __future__ import annotations
from datetime import date, datetime

from storage.database import (
    init_db, filter_new, save_repos, mark_featured,
    get_issue_number, log_email, get_total_seen,
)
from scrapers.github_trending import scrape_all_trending
from scrapers.github_search   import scrape_all_searches
from scrapers.github_enricher import enrich_batch
from scoring  import rank_and_filter, QUALITY_THRESHOLD
from writer   import select_top_repos, write_repo_story, write_closing
from emailer  import build_email_html, send_email
from config   import EMAIL_TO, MAX_STORIES, MIN_STORIES


def run():
    print()
    print("=" * 60)
    print("  AI GITHUB PULSE — Daily Repo Intelligence")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)
    print()

    init_db()
    issue = get_issue_number()
    print(f"  Issue #{issue:03d}  |  All-time DB: {get_total_seen()} repos seen")
    print()

    # ─── 1. SCRAPE ────────────────────────────────────────────────
    print("  [1/6] Scraping GitHub Trending + Search...")
    all_repos = []

    print("  -> github.com/trending (all languages + Python/TS/Rust/Go)")
    trending = scrape_all_trending()
    all_repos.extend(trending)

    print("  -> GitHub Search API (AI/agent/MCP/claude topics, 1k+ stars)")
    searched = scrape_all_searches()
    # Merge: if trending already has the repo, add stars_today to search result
    trending_map = {r["full_name"]: r for r in trending}
    for repo in searched:
        fn = repo["full_name"]
        if fn in trending_map:
            repo["stars_today"] = trending_map[fn].get("stars_today", 0)
        all_repos.append(repo)

    # Deduplicate by full_name, keep highest stars_today
    seen_fn: dict[str, dict] = {}
    for repo in all_repos:
        fn = repo["full_name"]
        if fn not in seen_fn or repo.get("stars_today", 0) > seen_fn[fn].get("stars_today", 0):
            seen_fn[fn] = repo
    all_repos = list(seen_fn.values())
    print(f"\n  Total unique repos: {len(all_repos)}")

    # ─── 2. DELTA FILTER ─────────────────────────────────────────
    print("\n  [2/6] Filtering already-featured repos...")
    new_repos = filter_new(all_repos)   # check first
    save_repos(all_repos)               # then record all as seen
    print(f"  New (never featured): {len(new_repos)}")

    if not new_repos:
        print("  Nothing new today. Skipping email.")
        log_email(issue, [], False, "No new repos")
        return

    # ─── 3. ENRICH ───────────────────────────────────────────────
    print("\n  [3/6] Enriching with GitHub API (commit velocity, fork ratio)...")
    # Pre-sort by rough signal before enriching to focus API calls
    new_repos.sort(key=lambda r: r.get("stars_today", 0) + r.get("stars", 0) // 1000, reverse=True)
    new_repos = enrich_batch(new_repos, max_enrich=35)
    print(f"  Enriched top 35 repos")

    # ─── 4. SCORE + FILTER ───────────────────────────────────────
    print("\n  [4/6] Composite scoring...")
    qualified = rank_and_filter(new_repos)
    print(f"  Qualified (score ≥ {QUALITY_THRESHOLD}): {len(qualified)}")

    if not qualified:
        print("  No repos cleared quality bar. Skipping email.")
        log_email(issue, [], False, f"Nothing above score {QUALITY_THRESHOLD}")
        return

    print("  Top 5:")
    for r in qualified[:5]:
        bd = r.get("score_breakdown", {})
        print(f"    [{r['composite_score']}] {r['full_name']:<45} +{r.get('stars_today',0)} today")
        print(f"         topic={bd.get('topic',0)} prestige={bd.get('prestige',0)} "
              f"velocity={bd.get('velocity',0)} momentum={bd.get('momentum',0)}")

    # ─── 5. SELECT + WRITE ───────────────────────────────────────
    print(f"\n  [5/6] Claude selects {MIN_STORIES}-{MAX_STORIES} and writes stories...")
    top_candidates = qualified[:15]
    selected = select_top_repos(top_candidates, qualified_count=len(qualified))
    n = len(selected)
    print(f"  Selected: {n}")

    stories = []
    for i, repo in enumerate(selected, 1):
        print(f"  Writing {i}/{n}: {repo['full_name']}...")
        stories.append(write_repo_story(repo, i))

    closing = write_closing(stories, len(all_repos))

    # ─── 6. EMAIL ────────────────────────────────────────────────
    print(f"\n  [6/6] Sending to {EMAIL_TO}...")
    today_str = date.today().strftime("%B %d, %Y")
    subject = (
        f"AI GitHub Pulse #{issue:03d} — {today_str} | "
        f"{n} must-see repo{'s' if n!=1 else ''} from {len(all_repos)} scanned"
    )

    html = build_email_html(
        issue=issue,
        stories=stories,
        closing=closing,
        total_scanned=len(all_repos),
        new_today=len(new_repos),
    )

    try:
        send_email(html, subject)
        mark_featured(selected)
        log_email(issue, [s["full_name"] for s in stories], True)
        print(f"\n  Issue #{issue:03d} sent. {n} repos.")
    except Exception as e:
        log_email(issue, [], False, str(e))
        print(f"  Send failed: {e}")
        raise

    print()
    print("  Done. See you tomorrow.")
    print()


if __name__ == "__main__":
    run()
