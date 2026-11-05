"""Thin client of the normkompass HTTP API."""

from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from .config import ASK_TIMEOUT_SECONDS, SEARCH_TIMEOUT_SECONDS
from .models import AskResponse, Passage, SearchResponse


class ClientError(Exception):
    """A failure the agent can be told about: the message is short, plain and has no trace."""


class AskNotConfigured(ClientError):
    """The API has no answer model configured."""


class NormkompassClient:
    """Calls /search and /ask; holds no state and sends nothing until a method is called."""

    def __init__(self, base_url: str, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._base_url = base_url
        self._transport = transport

    async def search(self, question: str, limit: int) -> list[Passage]:
        data = await self._post(
            "/search", {"question": question, "limit": limit}, SEARCH_TIMEOUT_SECONDS
        )
        return _parse(SearchResponse, data).results

    async def ask(self, question: str) -> AskResponse:
        data = await self._post("/ask", {"question": question}, ASK_TIMEOUT_SECONDS)
        return _parse(AskResponse, data)

    async def _post(self, path: str, body: dict[str, Any], seconds: float) -> object:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=seconds, transport=self._transport
            ) as http:
                response = await http.post(path, json=body)
        except httpx.TimeoutException as error:
            raise ClientError(
                f"The normkompass API at {self._base_url} "
                f"did not answer within {seconds:.0f} seconds."
            ) from error
        except httpx.TransportError as error:
            raise ClientError(
                f"The normkompass API at {self._base_url} is not reachable. "
                "Tell the user to start it (see the normkompass README) "
                "or to check NORMKOMPASS_API_URL."
            ) from error

        if response.status_code == 503 and path == "/ask":
            raise AskNotConfigured(
                "Answering is not configured on the normkompass side (no answer model is set up). "
                "search_law still works."
            )
        if response.status_code == 400:
            raise ClientError(f"The normkompass API rejected the request: {_message(response)}")
        if response.status_code != 200:
            raise ClientError(
                f"The normkompass API answered with an unexpected status {response.status_code}."
            )
        try:
            return response.json()
        except ValueError as error:
            raise ClientError(
                "The normkompass API returned a response that is not JSON."
            ) from error


def _message(response: httpx.Response) -> str:
    try:
        payload = response.json()
        message = payload.get("message") if isinstance(payload, dict) else None
    except ValueError:
        message = None
    if isinstance(message, str):
        return message[:200]
    if isinstance(message, list):
        return "; ".join(str(m) for m in message)[:200]
    return "invalid request"


def _parse[T: BaseModel](model: type[T], data: object) -> T:
    try:
        return model.model_validate(data)
    except ValidationError as error:
        raise ClientError(
            "The normkompass API returned a response in an unexpected shape; "
            "this server may not match the API version."
        ) from error
