"""
短期记忆：记录当前会话的消息历史，以支持多轮对话。常见策略包括：

消息裁剪Trimming：移除历史消息中的部分内容。
消息摘要Summarization：对历史消息进行概括整理。
删除消息：永久从内存状态中移除选定的消息。
长期记忆：存储用户或应用特定的数据，以跨会话记住用户偏好或其他信息。

实现方法：

使用 InMemorySaver 和 StateGraph 管理短期记忆。
使用 InMemoryStore 和 StateGraph 实现长期记忆。
提供基于裁剪和摘要的具体代码示例，以优化消息历史管理。
删除无效或冗余的消息记录以优化性能。
其他功能：

支持边缘案例（如“工具调用后必须有结果”）。
提供了删除所有消息和删除特定消息的具体代码示例。
"""

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from langchain_core.messages.utils import (
    trim_messages,
    count_tokens_approximately
)
from langchain_core.messages import RemoveMessage, REMOVE_ALL_MESSAGES
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, MessagesState
from langmem.short_term import SummarizationNode

model = init_chat_model("anthropic:claude-3-7-sonnet-latest")
summarization_model = model.bind(max_tokens=128)


# Delte messages
def delete_messages(state):
    messages = state["messages"]
    if len(messages) > 2:
        # remove the earliest two messages
        # return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *updated_messages]}
        return {"messages": [RemoveMessage(id=m.id) for m in messages[:2]]}


# Summarize messages
summarization_node = SummarizationNode(
    token_counter=count_tokens_approximately,
    model=summarization_model,
    max_tokens=512,
    max_tokens_before_summary=256,
    max_summary_tokens=256,
)


# Trim Messages
def call_model(state: MessagesState):
    messages = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=128,
        start_on="human",
        end_on=("human", "tool"),
    )
    response = model.invoke(messages)
    return {"messages": [response]}


checkpointer = InMemorySaver()
store = InMemoryStore()

builder = StateGraph(MessagesState)
builder.add_node(call_model)
builder.add_edge(START, "call_model")

# Long-term memory
# graph = builder.compile(checkpointer=checkpointer, store=store)
# Short-term memory
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "1"}}
graph.invoke({"messages": "hi, my name is bob"}, config)
graph.invoke({"messages": "write a short poem about cats"}, config)
graph.invoke({"messages": "now do the same but for dogs"}, config)
final_response = graph.invoke({"messages": "what's my name?"}, config)

final_response["messages"][-1].pretty_print()