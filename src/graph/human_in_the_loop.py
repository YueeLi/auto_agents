from hmac import new
from typing import Literal, final
from langgraph.types import Command,interrupt
from langchain_core.messages import HumanMessage
from langgraph.prebuilt.chat_agent_executor import AgentState
from src.graph.utils import build_image
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import uuid


class MyState(AgentState):
    seed: str


graph = StateGraph(MyState)


def first_node(state: MyState):
    print("--- Executing first_node ---")
    return {"messages": [HumanMessage(content="Message from first node")]}


def human_in_the_loop(state: MyState):
    print("--- Pausing for human input ---")
    print(f"User input: {state}")


def finish(state: MyState):
    print("--- Executing finish node ---")
    return {"messages": [HumanMessage(content="Message from finish node")]}


def node4(state: MyState):
    pass


def node5(state: MyState):
    pass


# 通过Commond来做分子判断
def jump(state: MyState) -> Command[Literal["node4", "node5"]]:
    print("--- Executing jump node ---")
    if len(state["messages"]) > 1:
        return Command(goto="node4")
    return Command(goto="node5")


graph.add_node("first_node", first_node)
graph.add_node("human_in_the_loop", human_in_the_loop)
graph.add_node("jump", jump)
graph.add_node("node4", node4)
graph.add_node("node5", node5)
graph.add_node("finish", finish)

graph.add_edge(START, "first_node")
graph.add_edge("first_node", "human_in_the_loop")

# 通过条件边来做判断
graph.add_conditional_edges(
    "human_in_the_loop",
    lambda state: "jump" if state["messages"][-1].content == "jump" else "finish",
    {
        "jump": "jump",
        "finish": "finish",
    }
)
graph.add_edge("node4", END)
graph.add_edge("node5", END)
graph.add_edge("finish", END)

memory = MemorySaver()
new_graph = graph.compile(name="human_in_the_loop", checkpointer=memory)
build_image(new_graph)

thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

# Step 1: Run the graph until it interrupts
events = new_graph.stream(
    {"messages": []},
    config=config,
)
for event in events:
    pass

# Step 2: Resume the graph with a command
print("--- Resuming graph execution ---")
resume_events = new_graph.stream(
    Command(resume={"type": "reject", "content": "how are you?"}),
    config=config,
)
for event in resume_events:
    pass
