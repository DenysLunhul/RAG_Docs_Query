from typing import Annotated
import requests
from langchain_core.tools import tool
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain_aws import ChatBedrock



@tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1}
    ).json()

    if not geo.get("results"):
        return f"Could not find city: {city}"

    lat = geo["results"][0]["latitude"]
    lon = geo["results"][0]["longitude"]

    weather = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": lat, "longitude": lon, "current_weather": True}
    ).json()

    temp = weather["current_weather"]["temperature"]
    return f"{city}: {temp}°C"



@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"Error: {e}"


tools_by_name = {"get_weather": get_weather, "calculator": calculator}



class State(BaseModel):
    messages: Annotated[list, add_messages] = []
    answer: str = ""



def agent_node(state: State) -> dict:
    response = llm_with_tools.invoke(state.messages)
    updates = {"messages": [response]}
    if not response.tool_calls:
        updates["answer"] = response.content
    return updates

def route_after_agent(state: State) -> str:
    last_msg = state.messages[-1]
    if last_msg.tool_calls:
        return "tools"
    return "end"

def tools_node(state: State) -> dict:
    last_msg = state.messages[-1]
    results = []
    for call in last_msg.tool_calls:
        fn = tools_by_name[call["name"]]
        result = fn.invoke(call["args"])
        results.append({"role": "tool", "content": result,
                        "tool_call_id": call["id"]})
    return {"messages": results}


llm = ChatBedrock(
    model_id="eu.anthropic.claude-haiku-4-5-20251001-v1:0",
    region_name="eu-north-1"
)
llm_with_tools = llm.bind_tools([get_weather, calculator])


graph = StateGraph(State)

graph.add_node("agent", agent_node)
graph.add_node("tools", tools_node)

graph.set_entry_point("agent")
graph.add_conditional_edges("agent", route_after_agent, {"tools": "tools", "end": END})
graph.add_edge("tools", "agent")

checkpointer = InMemorySaver()
app = graph.compile(checkpointer=checkpointer)




config = {"configurable": {"thread_id": "1"}}


while True:
    question = input("Enter question or Enter to end session: ")
    if not question:
        break
    result = app.invoke({"messages": [{"role": "user", "content": question}]}, config=config)
    print(result["answer"])
    print("-" * 50)

