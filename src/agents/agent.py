from pyexpat import model
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from typing_extensions import Annotated, TypedDict

from src.llms import get_llm_by_type

from langchain_core.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langchain_core.messages.utils import (
    trim_messages, 
    count_tokens_approximately
)
from langmem.short_term import SummarizationNode



# This function will be added as a new node in ReAct agent graph
# that will run every time before the node that calls the LLM.
# The messages returned by this function will be the input to the LLM.
def trim_messages_with_untouched(state):
    trimmed_messages = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=5000,
        start_on="human",
        end_on=("human", "tool"),
    )
    # To keep the original message history unmodified in the graph state,
    # we pass the updated history only as the input to the LLM, 
    # return updated messages under `llm_input_messages` key
    return {"llm_input_messages": trimmed_messages}



def trim_messages_with_modified(state):
    trimmed_messages = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=5000,
        start_on="human",
        end_on=("human", "tool"),
    )
    # NOTE that we're now returning the messages under the `messages` key
    # We also remove the existing messages in the history to ensure we're overwriting the history
    return {"messages": [RemoveMessage(REMOVE_ALL_MESSAGES)] + trimmed_messages}


model = get_llm_by_type("basic")

summarization_node = SummarizationNode(
        token_counter=count_tokens_approximately,
        model=model,
        max_tokens=5000,
        max_summary_tokens=1000,
        output_messages_key="llm_input_messages",
    )
    

def print_stream(stream, output_messages_key="llm_input_messages"):
    for chunk in stream:
        for node, update in chunk.items():
            print(f"Update from node: {node}")
            messages_key = (
                output_messages_key if node == "pre_model_hook" else "messages"
            )
            for message in update[messages_key]:
                if isinstance(message, tuple):
                    print(message)
                else:
                    message.pretty_print()

        print("\n\n")


