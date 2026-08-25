"""Free deterministic event classification based on ordered keyword rules."""

from __future__ import annotations

from dataclasses import replace

from backend.models.event import Event
from backend.utils.text import normalize_text

CATEGORY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Artificial Intelligence",
        (
            "artificial intelligence",
            "inteligencia artificial",
            "generative ai",
            "machine learning",
            "deep learning",
            "foundation model",
            "large language model",
            "amazon bedrock",
            "sagemaker",
            "gemini",
            "llm",
            "agents",
            "agentic",
            "ai",
            "ia",
            "claude",
            "cursor",
            "model context protocol",
            "mcp",
        ),
    ),
    (
        "Cybersecurity",
        (
            "cybersecurity",
            "ciberseguridad",
            "security",
            "seguridad",
            "devsecops",
            "zero trust",
            "iam",
        ),
    ),
    (
        "Data",
        (
            "data science",
            "data engineering",
            "analytics",
            "database",
            "big data",
            "sql",
            "postgresql",
            "power bi",
        ),
    ),
    (
        "DevOps",
        (
            "devops",
            "kubernetes",
            "docker",
            "terraform",
            "ci cd",
            "observability",
            "platform engineering",
        ),
    ),
    (
        "Mobile",
        ("mobile", "android", "ios", "flutter", "react native", "expo"),
    ),
    (
        "Web Development",
        (
            "web development",
            "frontend",
            "front end",
            "backend",
            "full stack",
            "react",
            "angular",
            "javascript",
            "typescript",
            "auth",
            "realtime app",
            "realtime apps",
            "saas",
            "seo",
            "aeo",
            "vercel",
            "remotion",
        ),
    ),
    (
        "Blockchain",
        ("blockchain", "web3", "smart contract", "ethereum", "solana"),
    ),
    (
        "Networking",
        ("networking", "network", "redes", "vpc", "dns"),
    ),
    (
        "IoT",
        ("internet of things", "iot", "embedded", "robotics", "robotica"),
    ),
    (
        "Cloud",
        (
            "cloud",
            "aws",
            "amazon web services",
            "azure",
            "gcp",
            "google cloud",
            "serverless",
            "lambda",
        ),
    ),
    (
        "Programming",
        (
            "programming",
            "programacion",
            "software development",
            "python",
            "java",
            "golang",
            "rust",
            "coding",
            "computacion grafica",
            "as code",
            "engineering",
        ),
    ),
    (
        "Entrepreneurship",
        ("entrepreneurship", "emprendimiento", "startup", "founder", "pitch"),
    ),
    (
        "Technology",
        (
            "technology",
            "tecnologia",
            "developer",
            "software",
            "innovation",
            "notion",
            "second brain",
            "hackathon",
            "meetup",
            "conference",
            "workshop",
            "build night",
        ),
    ),
)

TAG_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("AI", ("artificial intelligence", "inteligencia artificial", "generative ai", "llm", "agentic", "ai", "ia", "claude", "cursor", "mcp")),
    ("Machine Learning", ("machine learning", "deep learning", "sagemaker")),
    ("AWS", ("aws", "amazon web services", "bedrock", "lambda")),
    ("Azure", ("azure",)),
    ("Google Cloud", ("gcp", "google cloud")),
    ("Python", ("python",)),
    ("JavaScript", ("javascript", "typescript", "react", "angular")),
    ("Mobile", ("mobile", "android", "ios", "flutter", "react native", "expo")),
    ("Data", ("data", "analytics", "database", "sql")),
    ("Security", ("security", "seguridad", "cybersecurity", "ciberseguridad")),
    ("DevOps", ("devops", "kubernetes", "docker", "terraform", "ci cd")),
    ("Serverless", ("serverless", "lambda")),
    ("Startup", ("startup", "founder", "emprendimiento")),
)


def classify_event(event: Event) -> Event:
    """Return a classified copy without changing source-owned event fields."""
    primary_text = normalize_text(
        " ".join(
            (
                event.title,
                event.description or "",
                event.organization or "",
                event.event_type or "",
            )
        )
    )
    searchable = normalize_text(f"{primary_text} {' '.join(event.tags)}")
    category = next(
        (
            category
            for category, keywords in CATEGORY_RULES
            if any(_contains(primary_text, keyword) for keyword in keywords)
        ),
        next(
            (
                category
                for category, keywords in CATEGORY_RULES
                if any(_contains(searchable, keyword) for keyword in keywords)
            ),
            "Other",
        ),
    )
    inferred_tags = [
        tag
        for tag, keywords in TAG_RULES
        if any(_contains(searchable, keyword) for keyword in keywords)
    ]
    category_tag = [] if category == "Other" else [category]
    tags = list(dict.fromkeys([*event.tags, *category_tag, *inferred_tags]))
    return replace(event, category=category, tags=tags)


def classify_events(events: list[Event]) -> list[Event]:
    return [classify_event(event) for event in events]


def _contains(searchable: str, keyword: str) -> bool:
    normalized_keyword = normalize_text(keyword)
    return f" {normalized_keyword} " in f" {searchable} "

