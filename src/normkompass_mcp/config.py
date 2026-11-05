"""Configuration: one environment variable, no secrets."""

import os

DEFAULT_API_URL = "http://localhost:3000"
ENV_API_URL = "NORMKOMPASS_API_URL"

# normkompass limits, checked here first so the agent gets a clear message
# without a round trip.
MAX_QUESTION_LENGTH = 1000
MIN_LIMIT = 1
MAX_LIMIT = 20
DEFAULT_LIMIT = 5

SEARCH_TIMEOUT_SECONDS = 30.0
# Answering calls a language model, which can take much longer than a search.
ASK_TIMEOUT_SECONDS = 120.0


def api_url() -> str:
    """The configured normkompass address, without a trailing slash."""
    value = os.environ.get(ENV_API_URL, "").strip() or DEFAULT_API_URL
    return value.rstrip("/")
