
import uuid
from typing import Annotated, List, Literal, Optional, TypedDict, Any, Dict
from src.graph.utils import build_image
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage


# --- Sub-Graph Definition ---

class SubGraphState(TypedDict):
    """State for the sub-graph."""
    messages: Annotated[List[BaseMessage], add_messages]

def sub_graph_tool_node(state: SubGraphState) -> Dict[str, Any]:
    """A dummy tool node for the sub-graph."""
    print("--- (Sub-graph) Executing Tool Node ---")
    return {"messages": [AIMessage(content="Tool execution finished.")]}

def sub_graph_agent_node(state: SubGraphState) -> Dict[str, Any]:
    """A mock agent for the sub-graph that simulates a tool call."""
    print("--- (Sub-graph) Executing Agent Node ---")
    return {"messages": [AIMessage(content="I need to use a tool.")]}

def should_call_tool(state: SubGraphState) -> Literal["tool_node", END]:
    """Conditional edge to decide if the tool is needed."""
    print("--- (Sub-graph) Checking if tool is needed ---")
    if isinstance(state["messages"][-1], AIMessage):
        return "tool_node"
    return END

def create_chat_agent_graph():
    """Creates and compiles the sub-graph."""
    graph_builder = StateGraph(SubGraphState)
    graph_builder.add_node("agent", sub_graph_agent_node)
    graph_builder.add_node("tool_node", sub_graph_tool_node)
    graph_builder.set_entry_point("agent")
    graph_builder.add_conditional_edges("agent", should_call_tool)
    graph_builder.add_edge("tool_node", END)
    # This sub-graph runs to completion without interrupting.
    graph = graph_builder.compile(checkpointer=MemorySaver(), name="SubGraph")
    build_image(graph)
    return graph


# --- Main Graph Definition ---

class ComplexAgentState(TypedDict):
    """The main state for our complex graph."""
    messages: Annotated[List[BaseMessage], add_messages]
    human_approval_status: Optional[Literal["approved", "rejected"]]
    edit_content: Optional[str]
    validation_count: int

def initial_task_setup(state: ComplexAgentState) -> Dict[str, Any]:
    print("1. Executing Node: initial_task_setup")
    return {
        "messages": [AIMessage(content="Initial draft is ready for review.")],
        "validation_count": 0,
    }

def request_human_approval(state: ComplexAgentState) -> None:
    print("2. Executing Node: request_human_approval")
    if state.get("human_approval_status") in ["approved", "rejected"]:
        return
    print("   - Pausing for human approval.")
    interrupt(value=None)

def route_after_approval(state: ComplexAgentState) -> Literal["perform_action_approved", "request_human_edit"]:
    print("3. Executing Edge: route_after_approval")
    status = state["human_approval_status"]
    print(f"   - Routing based on status: '{status}'")
    return "perform_action_approved" if status == "approved" else "request_human_edit"

def request_human_edit(state: ComplexAgentState) -> Dict[str, Any]:
    print("4. Executing Node: request_human_edit")
    if state.get("edit_content"):
        print("   - Edit received. Applying changes.")
        return {"messages": [AIMessage(content=f"Applied edit: {state['edit_content']}")]}
    print("   - Pausing for human to provide edits.")
    interrupt(value=None)
    return {}

def perform_action_approved(state: ComplexAgentState) -> Dict[str, Any]:
    print("5a. Executing Node: perform_action_approved")
    print("   - Invoking sub-graph...")
    sub_graph = create_chat_agent_graph()
    sub_graph_result = sub_graph.invoke(
        {"messages": [HumanMessage(content="Start sub-task")]}
    )
    print("   - Sub-graph execution finished.")
    return {"messages": sub_graph_result["messages"]}

def multi_turn_validation(state: ComplexAgentState) -> Dict[str, Any]:
    print("6. Executing Node: multi_turn_validation")
    count = state.get("validation_count", 0)
    if count < 2:
        print(f"   - Pausing for validation step {count + 1}.")
        interrupt(value=None)
        return {"validation_count": count + 1}
    print("   - All validation steps completed.")
    return {}

def final_summary(state: ComplexAgentState) -> Dict[str, Any]:
    print("7. Executing Node: final_summary")
    return {"messages": [AIMessage(content="Process finished successfully.")]}

# --- Graph Construction ---
graph_builder = StateGraph(ComplexAgentState)
graph_builder.add_node("initial_task_setup", initial_task_setup)
graph_builder.add_node("request_human_approval", request_human_approval)
graph_builder.add_node("request_human_edit", request_human_edit)
graph_builder.add_node("perform_action_approved", perform_action_approved)
graph_builder.add_node("multi_turn_validation", multi_turn_validation)
graph_builder.add_node("final_summary", final_summary)

graph_builder.set_entry_point("initial_task_setup")
graph_builder.add_edge("initial_task_setup", "request_human_approval")
graph_builder.add_conditional_edges("request_human_approval", route_after_approval)
graph_builder.add_edge("request_human_edit", "multi_turn_validation")
graph_builder.add_edge("perform_action_approved", "multi_turn_validation")

def should_summarize(state: ComplexAgentState) -> Literal["final_summary", "__end__"]:
    if state.get("validation_count", 0) >= 2:
        return "final_summary"
    return "__end__" # Should not happen in this logic, but good practice

graph_builder.add_conditional_edges(
    "multi_turn_validation",
    should_summarize,
    {
        "final_summary": "final_summary",
        "__end__": END
    }
)
graph_builder.add_edge("final_summary", END)

compiled_graph = graph_builder.compile(checkpointer=MemorySaver(), name="MainGraph")

# --- Simulation of Step-by-Step Execution ---
if __name__ == "__main__":
    build_image(compiled_graph)

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print("="*50)
    print("🚀 Starting Graph Execution Simulation")
    print("="*50 + "\n")

    print("--- STEP 1: Initial Invocation ---")
    current_state = compiled_graph.invoke({}, config)
    print("   - INTERRUPT at 'request_human_approval'.\n")

    print("--- STEP 2: Resume with REJECTION ---")
    current_state = compiled_graph.invoke({"human_approval_status": "rejected"}, config)
    print("   - INTERRUPT at 'request_human_edit'.\n")

    print("--- STEP 3: Resume with Edited Content ---")
    current_state = compiled_graph.invoke({"edit_content": "This is the edited content."}, config)
    print("   - INTERRUPT at 'multi_turn_validation' (Step 1).\n")

    print("--- STEP 4: Resume from Validation Step 1 ---")
    current_state = compiled_graph.invoke(None, config)
    print("   - INTERRUPT at 'multi_turn_validation' (Step 2).\n")
    
    print("--- STEP 5: Resume from Validation Step 2 ---")
    final_state = compiled_graph.invoke(None, config)

    print("\n" + "="*50)
    print("✅ 'Rejected' Path Execution Finished")
    print("="*50)
    if final_state:
        print("Final Messages:")
        for msg in final_state.get("messages", []):
            print(f"- {msg.pretty_repr()}")

    print("\n\n" + "="*50)
    print("🚀 Starting 'Approved' Path Simulation")
    print("="*50 + "\n")
    
    thread_id_2 = str(uuid.uuid4())
    config_2 = {"configurable": {"thread_id": thread_id_2}}

    print("--- STEP 1 (Approved Path): Initial Invocation ---")
    current_state = compiled_graph.invoke({}, config_2)
    print("   - INTERRUPT at 'request_human_approval'.\n")

    print("--- STEP 2 (Approved Path): Resume with APPROVAL ---")
    current_state = compiled_graph.invoke({"human_approval_status": "approved"}, config_2)
    print("   - INTERRUPT at 'multi_turn_validation' (Step 1).\n")

    print("--- STEP 3 (Approved Path): Resume from Validation Step 1 ---")
    current_state = compiled_graph.invoke(None, config_2)
    print("   - INTERRUPT at 'multi_turn_validation' (Step 2).\n")

    print("--- STEP 4 (Approved Path): Resume from Validation Step 2 ---")
    final_state_2 = compiled_graph.invoke(None, config_2)

    print("\n" + "="*50)
    print("✅ 'Approved' Path Execution Finished")
    print("="*50)
    if final_state_2:
        print("Final Messages:")
        for msg in final_state_2.get("messages", []):
            print(f"- {msg.pretty_repr()}")
