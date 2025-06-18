from src.agents.agent import create_agent
from src.tools.crawl import web_crawler_tool
from src.tools.search import web_search_tool
from src.tools.python_repl import python_repl_tool
from src.config.agent_config import LLMType
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages

from langgraph.checkpoint.memory import MemorySaver


# 工具注册
TOOLS = [
    web_crawler_tool,  # 网站爬取
    web_search_tool,   # 网络搜索
    python_repl_tool,  # Python 代码执行
]

PROMPT_TEMPLATE = "chatbot"  # 对应 src/prompt/chatbot.md


# 定义聊天代理状态
class ChatAgentState(TypedDict):
    messages: Annotated[list, add_messages]


#创建 create_react_agent
llm = create_agent(
    tools=TOOLS,
    llm_type="basic",  # 使用基本模型
    template_name=PROMPT_TEMPLATE,  # 使用聊天机器人模板
)

# 创建聊天代理状态图
chat_agent_graph = StateGraph(ChatAgentState)
chat_agent_graph.add_node("chat", llm)
chat_agent_graph.set_entry_point("chat")

memory = MemorySaver()

config = {"configurable": {"thread_id": "1"}}

graph = chat_agent_graph.compile(checkpointer=memory)


def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}, config):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)


while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break