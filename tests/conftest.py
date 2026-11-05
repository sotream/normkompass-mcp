"""A stub of the normkompass API: the tests need no corpus, database or model."""

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

Handler = Callable[[httpx.Request], httpx.Response]


class StubApi:
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.handlers: dict[str, Handler] = {}

    def route(self, path: str, handler: Handler) -> None:
        self.handlers[path] = handler

    def respond(self, path: str, body: Any, status: int = 200) -> None:
        self.route(path, lambda _request: httpx.Response(status, json=body))

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        handler = self.handlers.get(request.url.path)
        if handler is None:
            return httpx.Response(404, json={"message": "Not Found"})
        return handler(request)

    def body(self, index: int = -1) -> dict[str, Any]:
        result: dict[str, Any] = json.loads(self.requests[index].content)
        return result

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self)


def passage(label: str, text: str = "Text") -> dict[str, Any]:
    return {
        "chunkId": "c1",
        "unitId": "ustg_1980/§ 14/Abs. 1",
        "part": 0,
        "source": "UStG",
        "path": ["§ 14", "Abs. 1"],
        "label": label,
        "title": "Ausstellung von Rechnungen",
        "url": "https://www.gesetze-im-internet.de/ustg_1980/__14.html",
        "stand": "UStG: zuletzt geändert durch Art. 5 G v. 29.6.2026 I Nr. 197",
        "text": text,
        "score": 0.03,
        "vectorRank": 1,
        "ftsRank": 2,
    }


ANSWER = {
    "answer": (
        "Ein Landfahrzeug gilt als neu, wenn es nicht mehr als 6.000 Kilometer zurückgelegt hat."
    ),
    "citations": [
        {
            "source": "UStG",
            "path": "§ 1b Abs. 3",
            "url": "https://www.gesetze-im-internet.de/ustg_1980/__1b.html",
            "quote": "nicht mehr als 6.000 Kilometer zurückgelegt hat",
        }
    ],
    "refused": False,
    "stand": "UStG: zuletzt geändert durch Art. 5 G v. 29.6.2026 I Nr. 197",
}

REFUSED = {"answer": "", "citations": [], "refused": True, "stand": None}


@pytest.fixture
def stub() -> StubApi:
    return StubApi()
