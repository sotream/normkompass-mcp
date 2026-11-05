"""Shapes of the normkompass API responses that the server relies on.

Unknown fields are ignored; a missing or mistyped field makes the response invalid.
"""

from pydantic import BaseModel, ConfigDict


class Passage(BaseModel):
    """One ranked passage of the corpus."""

    model_config = ConfigDict(extra="ignore")

    source: str
    label: str
    title: str
    url: str
    stand: str | None
    text: str


class SearchResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    results: list[Passage]


class Citation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source: str
    path: str
    url: str
    quote: str


class AskResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    answer: str
    citations: list[Citation]
    refused: bool
    stand: str | None
