import os
from dotenv import load_dotenv
load_dotenv()

REQUESTY_API_KEY = os.environ.get(
    "REQUESTY_API_KEY",
    "rqsty-sk-/JTViZRyS62Hdxsq1s2DGukrmTe4GTgjfmoT5ejWJ5ecV8UZuHFr14ZrEbXgCpt61QmZ6B+B/PFM4gx4o48A89xkEXANC+XfEllnEXUy7QA=",
)
REQUESTY_BASE_URL = "https://router.requesty.ai/v1"
REQUESTY_MODEL = "anthropic/claude-sonnet-4-6"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER", "lifeislovesam@gmail.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
EMAIL_TO   = os.environ.get("EMAIL_TO", "iamsamios@icloud.com")

MIN_STARS     = 1000
MAX_STORIES   = 5
MIN_STORIES   = 1
QUALITY_THRESHOLD = 25  # composite score floor

# Topics that make a repo must-see
TOPIC_SIGNALS = {
    "critical": [
        "agent", "agents", "agi", "autonomous-agent", "multi-agent",
        "mcp", "model-context-protocol", "agentic",
    ],
    "high": [
        "llm", "claude", "codex", "openai", "gemini", "gpt",
        "memory", "rag", "reasoning", "chain-of-thought",
        "copilot", "cursor", "terminal", "cli-tool",
    ],
    "medium": [
        "ai", "artificial-intelligence", "neural-network", "transformer",
        "langchain", "llamaindex", "vector-database", "embedding",
        "fine-tuning", "prompt-engineering", "alignment", "safety",
        "benchmark", "eval", "nlp", "generative-ai",
    ],
    "penalize": [
        "awesome", "list", "tutorial", "course", "bootcamp",
        "learning", "roadmap", "resources", "cheatsheet",
        "interview", "prep", "beginner",
    ],
}

# Orgs whose repos always get a prestige boost
PRESTIGE_ORGS = {
    "anthropics": 25, "anthropic": 25,
    "openai": 25, "google": 20, "google-deepmind": 25,
    "microsoft": 18, "meta-llama": 22, "facebookresearch": 20,
    "mistralai": 20, "huggingface": 18, "cohere-ai": 15,
    "eleutherai": 15, "allenai": 15, "stanfordnlp": 15,
    "langchain-ai": 18, "run-llama": 15, "chroma-core": 12,
    "mem0ai": 12, "crewaiinc": 15, "pydantic": 12,
}
