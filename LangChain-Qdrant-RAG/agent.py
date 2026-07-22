from dataclasses import dataclass
from typing import Annotated

from langchain.agents.middleware import SummarizationMiddleware
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain.agents.middleware.types import AgentMiddleware
from langchain.tools import tool, ToolRuntime
from langchain.agents import create_agent
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import add_messages
from pydantic import BaseModel

from app import (
    dense_model,
    sparse_model,
    reranker,
    COLLECTION_NAME,
    PREFETCH_LIMIT,
    RERANK_CANDIDATES,
    TOP_K,
    qdrant,
    models,
)


SYSTEM_PROMPT = (
    "You answer questions about documents the user has uploaded. "
    "Always use the retrieve tool to search the document(s) before answering — "
    "never answer from your own knowledge. "
    "If the retrieved passages don't contain the answer, say you don't know "
    "rather than guessing."
)
config = {"configurable": {"thread_id": 1}}


class State(BaseModel):
    messages: Annotated[list, add_messages] = []


@dataclass
class RetrievalConfig:
    use_hybrid: bool = False
    use_reranker: bool = False


class GroundingVerdict(BaseModel):
    grounded: bool


class GroundingCheckMiddleware(AgentMiddleware):
    """After the agent answers, checks the answer is backed by retrieved passages."""
    def __init__(self, judge_llm):
        super().__init__()
        self.judge_llm = judge_llm.with_structured_output(GroundingVerdict)

    def after_agent(self, state, runtime):
        messages = state["messages"]
        retrieved_context = "\n".join(
            m.content for m in messages if isinstance(m, ToolMessage)
        )
        final_answer = messages[-1].content

        if not retrieved_context or not final_answer:
            return None

        verdict = self.judge_llm.invoke(
            f"Retrieved context:\n{retrieved_context}\n\n"
            f"Answer:\n{final_answer}\n\n"
            "Is the answer fully supported by the retrieved context above? "
            "Answer only based on whether the claims in the answer appear in the context."
        )

        if verdict.grounded:
            return None

        return {
            "messages": [
                AIMessage(
                    content="Note: I could not fully verify the answer above against "
                    "the retrieved document passages — treat it with caution."
                )
            ]
        }


@tool
def retrieve(query: str, runtime: ToolRuntime) -> str:
    """Tool for retrieving information from documents"""
    dense_vector = dense_model.encode(query)

    HYBRID = runtime.context.use_hybrid
    RERANK = runtime.context.use_reranker

    if HYBRID:
        sparse_vector = next(sparse_model.embed([query]))
        points = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            prefetch=[
                models.Prefetch(query=dense_vector, using="dense", limit=PREFETCH_LIMIT),
                models.Prefetch(query=sparse_vector, using="sparse", limit=PREFETCH_LIMIT),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=RERANK_CANDIDATES if RERANK else TOP_K,
        )
    else:
        points = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=dense_vector,
            using="dense",
            limit=RERANK_CANDIDATES if RERANK else TOP_K,
        )

    if RERANK:
        points = points.points
        pairs = [(query, p.payload["text"]) for p in points]
        scores = reranker.predict(pairs)
        points = [p for p, _ in sorted(zip(points, scores), key=lambda x: x[1], reverse=True)][:TOP_K]
    else:
        points = points.points


    if not points:
        return "No relevant passages found in the document."

    return "\n\n".join(
        f"[{p.payload['doc_id']} p.{p.payload['page']}] {p.payload['text']}"
        for p in points
    )



llm = ChatBedrockConverse(
    model_id="eu.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name="eu-north-1"
)

agent = create_agent(
    model=llm,
    system_prompt=SYSTEM_PROMPT,
    tools=[retrieve],
    middleware=[
        ToolCallLimitMiddleware(
            tool_name="retrieve",
            run_limit=5,
            exit_behavior="continue"
        ),
        SummarizationMiddleware(
            model=llm,
            trigger=("messages", 40),
            keep=("messages", 20)
        ),
        GroundingCheckMiddleware(judge_llm=llm),
    ],
    state_schema=State,
    checkpointer=InMemorySaver(),
)


def ask(question: str, use_hybrid: bool = False, use_reranker: bool = False) -> str:
    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
        context=RetrievalConfig(use_hybrid=use_hybrid, use_reranker=use_reranker),
    )
    return result["messages"][-1].content