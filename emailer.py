"""
Builds and sends the AI GitHub Pulse email.
Dark theme, signal-rich, engineered for scanability.
"""
from __future__ import annotations
import re, smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_TO


def _md(text: str) -> str:
    """Minimal markdown → HTML."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#e2e8f0;">\1</strong>', text)
    text = re.sub(r'\*(.+?)\*',     r'<em style="color:#94a3b8;">\1</em>', text)
    text = re.sub(r'`([^`]+)`',     r'<code style="background:#1e293b;color:#a78bfa;padding:1px 5px;border-radius:3px;font-size:12px;">\1</code>', text)
    paras = text.split('\n\n')
    out = []
    for p in paras:
        p = p.strip()
        if not p:
            continue
        p = p.replace('\n', '<br>')
        if p.startswith('**'):
            out.append(f'<p style="color:#e2e8f0;font-size:15px;line-height:1.8;margin:14px 0;">{p}</p>')
        else:
            out.append(f'<p style="color:#cbd5e1;font-size:15px;line-height:1.8;margin:10px 0;">{p}</p>')
    return '\n'.join(out)


def _lang_badge(lang: str) -> str:
    colors = {
        "Python": "#3b82f6", "TypeScript": "#8b5cf6", "JavaScript": "#f59e0b",
        "Rust": "#ef4444", "Go": "#10b981", "C++": "#f97316", "C": "#6b7280",
    }
    color = colors.get(lang, "#64748b")
    return f'<span style="background:{color}22;color:{color};padding:2px 8px;border-radius:10px;font-size:10px;font-weight:600;">{lang}</span>' if lang else ''


def _star_badge(stars_today: int) -> str:
    if not stars_today:
        return ''
    emoji = "🔥" if stars_today >= 200 else "⭐"
    return f'<span style="background:#16a34a22;color:#4ade80;padding:2px 8px;border-radius:10px;font-size:10px;font-weight:600;">{emoji} +{stars_today} today</span>'


def build_story_html(story: dict) -> str:
    content_html = _md(story["content"])
    full_name = story.get("full_name", "")
    url = story.get("url", "#")
    stars = story.get("stars", 0)
    stars_today = story.get("stars_today", 0)
    language = story.get("language", "")
    score = story.get("score", 0)
    score_color = "#4ade80" if score >= 70 else "#a78bfa" if score >= 45 else "#818cf8"

    badges = " ".join(filter(None, [
        _lang_badge(language),
        _star_badge(stars_today),
    ]))

    return f"""
<div style="background:#0f172a;border-radius:12px;padding:24px;margin-bottom:20px;border:1px solid #1e293b;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
    <div>
      <a href="{url}" style="color:#e2e8f0;font-size:16px;font-weight:700;text-decoration:none;font-family:monospace;">{full_name}</a>
      <span style="color:#475569;font-size:12px;margin-left:10px;">⭐ {stars:,}</span>
    </div>
    <span style="color:{score_color};font-size:11px;font-weight:600;">signal: {score}</span>
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px;">{badges}</div>
  {content_html}
  <div style="margin-top:16px;padding-top:12px;border-top:1px solid #1e293b;">
    <a href="{url}" style="color:#6366f1;font-size:12px;text-decoration:none;font-weight:600;">View on GitHub →</a>
  </div>
</div>"""


def build_email_html(issue: int, stories: list[dict], closing: str, total_scanned: int, new_today: int) -> str:
    date_str = date.today().strftime("%B %d, %Y")
    day_name = date.today().strftime("%A")
    stories_html = "\n".join(build_story_html(s) for s in stories)
    n = len(stories)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:16px 0;background:#020817;font-family:'Inter',-apple-system,sans-serif;">
<div style="max-width:660px;margin:0 auto;">

<!-- Header -->
<div style="background:linear-gradient(135deg,#0f172a 0%,#1e1b4b 100%);padding:28px 32px 20px;border-radius:12px 12px 0 0;border-bottom:1px solid #1e293b;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
    <div>
      <p style="margin:0 0 4px;color:#6366f1;font-size:10px;letter-spacing:3px;text-transform:uppercase;font-weight:700;">Issue #{issue:03d}</p>
      <h1 style="margin:0;color:#f1f5f9;font-size:24px;font-weight:800;letter-spacing:-0.5px;">AI GitHub Pulse</h1>
      <p style="margin:6px 0 0;color:#475569;font-size:12px;">{day_name}, {date_str} · Daily AI Repo Intelligence</p>
    </div>
    <div style="text-align:right;">
      <p style="margin:0;color:#6366f1;font-size:28px;font-weight:800;">{n}</p>
      <p style="margin:2px 0 0;color:#475569;font-size:10px;">repos today</p>
      <p style="margin:4px 0 0;color:#334155;font-size:9px;">of {total_scanned} scanned</p>
    </div>
  </div>
</div>

<!-- Sub-header -->
<div style="background:#0a0f1e;padding:14px 32px;border-bottom:1px solid #1e293b;">
  <p style="margin:0;color:#64748b;font-size:12px;line-height:1.6;">
    Every day: scan GitHub Trending + Search across AI · agents · LLMs · Claude · Codex · terminal · memory · AGI.
    Score by star velocity, fork ratio, commit momentum, org prestige. Only what actually matters reaches your inbox.
  </p>
</div>

<!-- Stories -->
<div style="background:#020817;padding:24px 32px;">
  <h2 style="margin:0 0 20px;color:#94a3b8;font-size:11px;letter-spacing:2px;text-transform:uppercase;font-weight:600;">Today's {n} Must-See Repo{'s' if n!=1 else ''}</h2>
  {stories_html}
</div>

<!-- Closing -->
<div style="background:#0a0f1e;padding:20px 32px;border-top:1px solid #1e293b;border-radius:0 0 12px 12px;">
  <p style="margin:0 0 12px;color:#94a3b8;font-size:13px;line-height:1.7;font-style:italic;">{closing}</p>
  <p style="margin:16px 0 0;color:#334155;font-size:10px;">
    AI GitHub Pulse · Issue #{issue:03d} · {date_str}<br>
    Built by Anmol Chaudhary · <a href="https://github.com/originaonxi/ai-github-pulse" style="color:#6366f1;text-decoration:none;">github.com/originaonxi/ai-github-pulse</a>
  </p>
</div>

</div>
</body>
</html>"""


def send_email(html: str, subject: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SMTP_USER
    msg["To"]      = EMAIL_TO
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.sendmail(SMTP_USER, EMAIL_TO, msg.as_string())
