"""
To add runtime configuration:

Specify a schema for your configuration
Add the configuration to the function signature for nodes or conditional edges
Pass the configuration into the graph.
"""


from typing import Optional

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, MessagesState, StateGraph, START
from typing_extensions import TypedDict


class ConfigSchema(TypedDict):
    model: Optional[str]
    system_message: Optional[str]


MODELS = {
    "anthropic": init_chat_model("anthropic:claude-3-5-haiku-latest"),
    "openai": init_chat_model("openai:gpt-4.1-mini"),
}


def call_model(state: MessagesState, config: RunnableConfig):
    model = config["configurable"].get("model", "anthropic")
    model = MODELS[model]
    messages = state["messages"]
    if system_message := config["configurable"].get("system_message"):
        messages = [SystemMessage(system_message)] + messages
    response = model.invoke(messages)
    return {"messages": [response]}


builder = StateGraph(MessagesState, config_schema=ConfigSchema)
builder.add_node("model", call_model)
builder.add_edge(START, "model")
builder.add_edge("model", END)

graph = builder.compile()

# Usage
input_message = {"role": "user", "content": "hi"}
config = {"configurable": {"model": "openai", "system_message": "Respond in Italian."}}
response = graph.invoke({"messages": [input_message]}, config)
for message in response["messages"]:
    message.pretty_print()