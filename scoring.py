"""
Composite scoring for GitHub repos.
Signals: stars_today + topic match + org prestige + fork ratio + commit velocity + star count tier
"""
from __future__ import annotations
from config import TOPIC_SIGNALS, PRESTIGE_ORGS, MIN_STARS, QUALITY_THRESHOLD

# Hard exclusion patterns — these repos are noise
EXCLUDE_PATTERNS = [
    "awesome-", "awesome_", "-awesome", "tutorial", "course",
    "bootcamp", "learning", "roadmap", "cheatsheet", "interview",
    "beginner", "resources", "-list", "_list",
]


def is_excluded(repo: dict) -> bool:
    """Hard filter: remove noise before scoring."""
    name = repo.get("repo", "").lower()
    full = repo.get("full_name", "").lower()
    owner = repo.get("owner", "").lower()
    topics = [t.lower() for t in repo.get("topics", [])]

    # Reject non-repo GitHub paths (sponsors pages, orgs, etc.)
    if owner in ("sponsors", "orgs", "topics", "explore"):
        return True
    if not name or not owner or "/" not in repo.get("full_name", "/"):
        return True

    if repo.get("is_fork") or repo.get("is_archived") or repo.get("not_found"):
        return True
    if repo.get("stars", 0) < MIN_STARS and repo.get("stars_today", 0) < 50:
        return True

    for pat in EXCLUDE_PATTERNS:
        if pat in name or pat in full:
            return True
    if "awesome" in topics or "tutorial" in topics or "resources" in topics:
        return True

    # No commits in 90+ days is a dead project
    pushed = repo.get("pushed_at", "")
    if pushed:
        from datetime import datetime, timezone
        try:
            pushed_dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
            days_since = (datetime.now(timezone.utc) - pushed_dt).days
            if days_since > 90:
                return True
        except Exception:
            pass

    return False


def compute_topic_score(repo: dict) -> int:
    text = " ".join([
        repo.get("repo", ""),
        repo.get("description") or "",
        " ".join(repo.get("topics", [])),
    ]).lower()

    score = 0
    for kw in TOPIC_SIGNALS["critical"]:
        if kw in text:
            score += 20
    for kw in TOPIC_SIGNALS["high"]:
        if kw in text:
            score += 12
    for kw in TOPIC_SIGNALS["medium"]:
        if kw in text:
            score += 6
    for kw in TOPIC_SIGNALS["penalize"]:
        if kw in text:
            score -= 20
    return max(0, score)


def compute_org_prestige(repo: dict) -> int:
    owner = repo.get("owner", "").lower()
    return PRESTIGE_ORGS.get(owner, 0)


def compute_star_velocity_score(repo: dict) -> int:
    """Stars today = strongest real-time signal."""
    today = repo.get("stars_today", 0)
    if today >= 500:  return 40
    if today >= 200:  return 30
    if today >= 100:  return 22
    if today >= 50:   return 15
    if today >= 20:   return 8
    if today >= 5:    return 3
    return 0


def compute_star_tier_score(repo: dict) -> int:
    """Absolute star count — credibility signal."""
    stars = repo.get("stars", 0)
    if stars >= 50000: return 20
    if stars >= 20000: return 15
    if stars >= 10000: return 12
    if stars >= 5000:  return 8
    if stars >= 2000:  return 5
    if stars >= 1000:  return 2
    return 0


def compute_momentum_score(repo: dict) -> int:
    """Fork ratio + commit velocity = engineers are actually using it."""
    stars = repo.get("stars", 1)
    forks = repo.get("forks", 0)
    commits_4w = repo.get("commits_last_4w", 0)

    score = 0
    fork_ratio = forks / max(stars, 1)
    if fork_ratio >= 0.3:  score += 12
    elif fork_ratio >= 0.15: score += 8
    elif fork_ratio >= 0.05: score += 4

    if commits_4w >= 50:  score += 10
    elif commits_4w >= 20: score += 7
    elif commits_4w >= 5:  score += 4
    elif commits_4w >= 1:  score += 1

    return score


def compute_composite_score(repo: dict) -> int:
    topic    = compute_topic_score(repo)
    prestige = compute_org_prestige(repo)
    velocity = compute_star_velocity_score(repo)
    tier     = compute_star_tier_score(repo)
    momentum = compute_momentum_score(repo)

    total = topic + prestige + velocity + tier + momentum
    repo["composite_score"] = total
    repo["score_breakdown"] = {
        "topic": topic, "prestige": prestige,
        "velocity": velocity, "tier": tier, "momentum": momentum,
    }
    return total


def rank_and_filter(repos: list[dict]) -> list[dict]:
    """Remove noise, score everything, return qualified repos sorted by score."""
    qualified = []
    for repo in repos:
        if is_excluded(repo):
            continue
        score = compute_composite_score(repo)
        if score >= QUALITY_THRESHOLD:
            qualified.append(repo)

    qualified.sort(key=lambda x: x.get("composite_score", 0), reverse=True)
    return qualified
