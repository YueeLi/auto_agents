from src.llms.llm import get_llm_by_type, basic_llm
from src.tools import *
from src.config.llm_config import LLMType
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.types import interrupt, Command
import json
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
from src.graph.utils import build_image

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt.chat_agent_executor import AgentState


from langgraph.checkpoint.memory import MemorySaver


class MyState(AgentState):
    pass

chat_agent_graph = StateGraph(MyState)

TOOLS = [
    add_human_in_the_loop(python_repl_tool),
    add_human_in_the_loop(tavily_search),
    add_human_in_the_loop(tavily_web_crawl),
]

# llm = get_llm_by_type("reasoning").bind_tools(TOOLS)
llm = get_llm_by_type("basic").bind_tools(TOOLS)

def chat_node(state: MyState):
    return {"messages": [llm.invoke(state["messages"])]}


class BasicToolNode:
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}

def route_tools(
    state: MyState,
):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END

# The `tools_condition` function returns "tools" if the chatbot asks to use a tool, and "END" if
# it is fine directly responding. This conditional routing defines the main agent loop.
chat_agent_graph.add_conditional_edges(
    "chat",
    route_tools,
    # The following dictionary lets you tell the graph to interpret the condition's outputs as a specific node
    # It defaults to the identity function, but if you
    # want to use a node named something else apart from "tools",
    # You can update the value of the dictionary to something else
    # e.g., "tools": "my_tools"
    {"tools": "tools", END: END},
)


tool_node = BasicToolNode(tools=TOOLS)
chat_agent_graph.add_node("tools", tool_node)
chat_agent_graph.add_node("chat", chat_node)
chat_agent_graph.add_edge(START, "chat")
chat_agent_graph.add_edge("tools", "chat")



memory = MemorySaver()

graph = chat_agent_graph.compile(name="chat_agent", checkpointer=memory)
build_image(graph)


config = {"configurable": {"thread_id": "1"}, "recursion_limit": 10}

events = graph.stream(
    {"messages": [HumanMessage(content="写一段脚本计算 2.11111 + 3.22222")]},
    config=config,
)
for event in events:
    if "messages" in event:
        event["messages"][-1].pretty_print()


events = graph.stream(
    Command(resume = [{"type": "accept"}]),
    config=config,
)
