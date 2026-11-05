"""The MCP server: two tools over the normkompass API."""

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel

from .client import ClientError, NormkompassClient
from .config import DEFAULT_LIMIT, MAX_LIMIT, MAX_QUESTION_LENGTH, MIN_LIMIT, api_url
from .models import Citation, Passage

NOTE = (
    "German federal law (UStG, UStDV, AO, BDSG, DDG). Not legal advice. "
    "Every result carries the Stand (version date) of the law it comes from."
)

SEARCH_DESCRIPTION = (
    "Search the normkompass corpus and return the best matching passages, in the API's order, "
    "each with its citation label (for example '§ 14 Abs. 1 UStG'), title, source URL, "
    "Stand and text. Use it to find the exact passage before citing. " + NOTE
)

ASK_DESCRIPTION = (
    "Ask a question and get an answer with citations, or an explicit refusal when the corpus "
    "does not support an answer. normkompass checked that every quote in the citations is a "
    "verbatim part of a retrieved passage; this server adds nothing to it. Needs an answer "
    "model configured in normkompass. " + NOTE
)

REFUSAL_MESSAGE = (
    "normkompass found no answer that its citation check supports. This does not mean the law "
    "has no answer: try search_law to read the passages yourself, or rephrase the question."
)


class SearchResult(BaseModel):
    passages: list[Passage]


class AskResult(BaseModel):
    refused: bool
    answer: str
    citations: list[Citation]
    stand: str | None
    message: str | None


def _check_question(question: str) -> str:
    text = question.strip()
    if not text:
        raise ToolError('"question" must be a non-empty text.')
    if len(question) > MAX_QUESTION_LENGTH:
        raise ToolError(f'"question" must have at most {MAX_QUESTION_LENGTH} characters.')
    return text


def build_server(client: NormkompassClient | None = None) -> MCPServer:
    """Create the server. Nothing is requested from the API until a tool is called."""
    api = client or NormkompassClient(api_url())
    server = MCPServer(
        "normkompass",
        instructions=(
            "Tools for German federal law with verifiable citations (normkompass). "
            "Cite the returned citation labels and mention the Stand. Not legal advice."
        ),
    )

    @server.tool(name="search_law", description=SEARCH_DESCRIPTION)
    async def search_law(question: str, limit: int = DEFAULT_LIMIT) -> SearchResult:
        text = _check_question(question)
        if limit < MIN_LIMIT or limit > MAX_LIMIT:
            raise ToolError(f'"limit" must be an integer between {MIN_LIMIT} and {MAX_LIMIT}.')
        try:
            return SearchResult(passages=await api.search(text, limit))
        except ClientError as error:
            raise ToolError(str(error)) from error

    @server.tool(name="ask_law", description=ASK_DESCRIPTION)
    async def ask_law(question: str) -> AskResult:
        text = _check_question(question)
        try:
            response = await api.ask(text)
        except ClientError as error:
            raise ToolError(str(error)) from error
        if response.refused:
            return AskResult(
                refused=True, answer="", citations=[], stand=None, message=REFUSAL_MESSAGE
            )
        if not response.citations or not response.answer.strip():
            # normkompass never returns an answer without a verified citation: do not pass one on.
            raise ToolError(
                "The normkompass API returned an answer without a citation, which it should "
                "never do; the answer was discarded."
            )
        return AskResult(
            refused=False,
            answer=response.answer,
            citations=response.citations,
            stand=response.stand,
            message=None,
        )

    return server
