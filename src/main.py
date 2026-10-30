"""FastAPI service for the chemistry assistant."""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel, Field

from .config import settings
from .tools import TOOL_FUNCTIONS, get_mcp_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful chemistry assistant with access to a
knowledge graph of chemical entities and properties from Wikidata and Rhea.

Use the available tools to answer questions about reactions, chemical and
physical properties, substance classifications, and mixture components.
Be thorough but concise. If a tool returns an error or no result, say so and
suggest an alternative query. Mention Wikidata sources when relevant."""


def build_langchain_tools() -> list[StructuredTool]:
    """Wrap the async chemistry functions as LangChain tools."""
    tools = []

    for tool_definition in get_mcp_tools():
        function = TOOL_FUNCTIONS.get(tool_definition.name)
        if function is None:
            logger.warning("No function registered for tool %s", tool_definition.name)
            continue

        description = (
            tool_definition.description
            or function.__doc__
            or f"Call the {tool_definition.name} chemistry tool."
        )

        tools.append(
            StructuredTool.from_function(
                coroutine=function,
                name=tool_definition.name,
                description=description,
            )
        )

    return tools


def create_chemistry_agent(checkpointer: InMemorySaver):
    """Create the chemistry agent using KoboldCpp's OpenAI-compatible API."""
    base_url = settings.KOBOLD_API_URL.rstrip("/")
    if not base_url.endswith("/v1"):
        base_url += "/v1"

    model = ChatOpenAI(
        model=settings.KOBOLD_MODEL,
        base_url=base_url,
        api_key=settings.KOBOLD_API_KEY,
        temperature=0.7,
        max_tokens=512,
    )

    return create_agent(
        model=model,
        tools=build_langchain_tools(),
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create the agent at startup and release the app reference at shutdown."""
    checkpointer = InMemorySaver()
    app.state.agent = create_chemistry_agent(checkpointer)
    logger.info("Chemistry agent initialized")
    try:
        yield
    finally:
        app.state.agent = None
        logger.info("Chemistry agent stopped")


app = FastAPI(
    title="Chemistry LLM Service",
    version="1.0.0",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    conversation_id: str


def message_text(content: Any) -> str:
    """Convert an AI message's content to response text."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = [
            item["text"]
            for item in content
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        ]
        return "\n".join(text_parts)

    return str(content)


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="Message cannot be blank.")

    agent = getattr(app.state, "agent", None)
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent is not initialized.")

    try:
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config={
                "configurable": {
                    "thread_id": request.conversation_id,
                }
            },
        )

        for response_message in reversed(result["messages"]):
            if (
                isinstance(response_message, AIMessage)
                and not response_message.tool_calls
            ):
                return ChatResponse(
                    response=message_text(response_message.content),
                    conversation_id=request.conversation_id,
                )

        return ChatResponse(
            response="No response generated.",
            conversation_id=request.conversation_id,
        )

    except Exception as exc:
        logger.exception("Agent execution failed")
        raise HTTPException(
            status_code=502,
            detail="The chemistry agent failed to process the request.",
        ) from exc


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "agent_initialized": getattr(app.state, "agent", None) is not None,
        "chemistry_api": settings.CHEMISTRY_API_BASE,
        "kobold_api": settings.KOBOLD_API_URL,
    }
