# AI GitHub Pulse

**Every morning at 9am PST — the 1-5 GitHub repos every AI engineer needs to see today.**

Scans GitHub Trending + Search across AI · agents · LLMs · Claude · Codex · terminal · memory · AGI.
Scores by star velocity, fork ratio, commit momentum, and org prestige.
Claude writes the stories. Only what actually matters reaches your inbox.

## What it tracks

| Signal | Weight |
|--------|--------|
| Stars today (trending) | Strongest — real-time momentum |
| Topic match (agent/LLM/MCP/AGI/Claude) | Core filter |
| Org prestige (Anthropic/OpenAI/Meta/Google) | Credibility |
| Fork ratio (forks/stars) | Engineers actually using it |
| Commit velocity (last 4 weeks) | Active development |

## Hard filters

Automatically excluded:
- `awesome-*` lists, tutorials, courses, boilerplates
- Forks and archived repos
- No commits in 90+ days
- Under 1,000 stars (unless trending today)

## Email format per repo

- **Hook** — most surprising fact or exact problem solved
- **What it does** — technical approach, what makes it different
- **Why you should care** — concrete use case for builders
- **The signal** — traction naturally woven in

## Setup

```bash
git clone https://github.com/originaonxi/ai-github-pulse
cd ai-github-pulse
pip install -r requirements.txt
cp .env.example .env  # fill in your keys
python agent.py
```

## Cron (GitHub Actions)

Runs daily at **9:00 AM PST** via `.github/workflows/daily_pulse.yml`.
SQLite DB auto-commits back to repo for permanent deduplication.

Built by **Anmol Chaudhary**
