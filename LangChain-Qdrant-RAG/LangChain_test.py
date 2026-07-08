from langchain.agents import create_agent
from langchain_aws import ChatBedrockConverse
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.types import Command
from LangGraph_test import calculator, get_weather
from pydantic import BaseModel

class WeatherResponse(BaseModel):
    city: str
    temperature_celsius: float
    summary: str


llm = ChatBedrockConverse(
    model_id="eu.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name="eu-north-1"
)

agent = create_agent(
    model=llm,
    tools=[calculator, get_weather],
    middleware=[
        HumanInTheLoopMiddleware(interrupt_on={"calculator": True})
    ],
    checkpointer=InMemorySaver(),
    response_format=WeatherResponse
)

config = {"configurable": {"thread_id": "42"}}
result = agent.invoke({"messages": [{"role": "user", "content": "What is the weather in Lviv?"}]},
                      config=config)

interrupt_data = result.get("__interrupt__")

if interrupt_data:
    print(interrupt_data)

    decision = input("Approve calculator call? (y/n): ")

    if decision.lower() == "y":
        final_result = agent.invoke(
            Command(resume={"decisions": [{"type": "approve"}]}),
            config=config
        )
    else:
        reason = input("Reason for rejection: ")
        final_result = agent.invoke(
            Command(resume={"decisions": [{"type": "reject", "message": reason}]}),
            config=config
        )

    print(final_result["messages"][-1].content)
else:
    print(result.get("structured_response"))