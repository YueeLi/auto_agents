"""
LangGraph Memory 全面演示（基于官方 concepts/memory 与 how-tos/memory 整理）

知识点目录：
1. Memory 的基本概念与分类（短期记忆、长期记忆）
2. 短期记忆的用法与管理（State、Checkpointer、消息裁剪、reducer思想）
3. 长期记忆的用法与管理（Store、namespace+key、检索/更新/删除）
4. 管理长对话历史的技巧（按条数/按token裁剪、摘要、RemoveMessage等）
5. MemorySaver/InMemorySaver 的用法与注意事项
6. 外部 Memory 存储集成（如 Zep、向量数据库等）
7. 性能优化与最佳实践（对象复用、懒加载、profile、分层存储等）
8. 常见陷阱与注意事项（内存泄漏、线程隔离、数据一致性、消息合法性等）
9. 进阶技巧：自定义 reducer、混合存储、与人类交互结合、写入时机（hot path/background）
"""

# 1. Memory 的基本概念与分类
# - 短期记忆（Short-term）：线程/会话级，通常存储在 state，通过 checkpointer 持久化。
# - 长期记忆（Long-term）：跨线程/会话，通常存储在 store，支持 namespace+key 组织。

# 2. 短期记忆的用法与管理
class ShortTermMemory:
    def __init__(self):
        self.history = []
    def add_message(self, message):
        self.history.append(message)
    def get_history(self):
        return self.history

# reducer 风格的消息管理（官方推荐）
def manage_list(existing, updates):
    """
    官方推荐的 reducer 思路：
    - updates 可以是 list（追加），也可以是 dict（如 {type: 'keep', from: x, to: y}）
    """
    if isinstance(updates, list):
        return existing + updates
    elif isinstance(updates, dict) and updates.get("type") == "keep":
        return existing[updates["from"]:updates["to"]]
    return existing

# 3. 长期记忆的用法与管理
class LongTermMemory:
    def __init__(self):
        self.store = {}  # {(namespace, key): value}
    def put(self, namespace, key, value):
        self.store[(namespace, key)] = value
    def get(self, namespace, key):
        return self.store.get((namespace, key), None)
    def search(self, namespace, filter_func=None):
        results = [(k[1], v) for k, v in self.store.items() if k[0] == namespace]
        if filter_func:
            results = [item for item in results if filter_func(item[1])]
        return results
    def delete(self, namespace, key=None):
        if key:
            self.store.pop((namespace, key), None)
        else:
            to_del = [k for k in self.store if k[0] == namespace]
            for k in to_del:
                self.store.pop(k)

# 4. 管理长对话历史的技巧
class TruncatedMemory(ShortTermMemory):
    def __init__(self, max_length=10):
        super().__init__()
        self.max_length = max_length
    def add_message(self, message):
        if len(self.history) >= self.max_length:
            self.history.pop(0)
        self.history.append(message)

# 伪代码：按 token 裁剪（需依赖 langchain_core）
# from langchain_core.messages.utils import trim_messages, count_tokens_approximately
# messages = trim_messages(messages, strategy="last", token_counter=count_tokens_approximately, max_tokens=128)

# 伪代码：摘要策略
# def summarize_conversation(messages, summary=""):
#     prompt = f"This is a summary of the conversation to date: {summary}\\n\\nExtend the summary by taking into account the new messages above:"
#     # 用 LLM 生成新 summary
#     new_summary = llm.invoke(messages + [prompt])
#     # 删除早期消息，仅保留最近 N 条
#     return new_summary, messages[-2:]

# RemoveMessage/REMOVE_ALL_MESSAGES 伪代码
# from langchain_core.messages import RemoveMessage
# from langgraph.graph.message import REMOVE_ALL_MESSAGES
# 删除指定消息：return {"messages": [RemoveMessage(id=msg_id)]}
# 删除全部消息：return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES)]}

# 5. MemorySaver/InMemorySaver 的用法与注意事项
# from langgraph.checkpoint.memory import InMemorySaver
# checkpointer = InMemorySaver()
# graph = builder.compile(checkpointer=checkpointer)

# 6. 外部 Memory 存储集成
# from zep_cloud.client import AsyncZep
# zep = AsyncZep(api_key=...)
# await zep.save_message(thread_id, message)
# messages = await zep.get_messages(thread_id)

# 7. 性能优化与最佳实践
# - 对象复用、懒加载、profile、分层存储、token 裁剪、摘要等

# 8. 常见陷阱与注意事项
# - 内存泄漏、线程隔离、数据一致性、消息合法性（如 LLM 历史必须以 user 开头等）

# 9. 进阶技巧
# - 自定义 reducer、混合存储、与 human-in-the-loop 结合
# - 写入记忆时机：主流程写入（hot path）/后台写入（background）

class HybridMemory:
    def __init__(self, max_short=5):
        self.short = TruncatedMemory(max_length=max_short)
        self.long = LongTermMemory()
    def add_message(self, namespace, key, message):
        self.short.add_message(message)
        self.long.put(namespace, key, message)
    def get_short_history(self):
        return self.short.get_history()
    def get_long_history(self, namespace, key):
        return self.long.get(namespace, key)

# 用法示例：
if __name__ == "__main__":
    print("---短期记忆---")
    stm = ShortTermMemory()
    stm.add_message("User: Hello!")
    stm.add_message("AI: Hi, how can I help you?")
    print(stm.get_history())

    print("---长期记忆---")
    ltm = LongTermMemory()
    ltm.put("user_123", "profile", {"name": "Bob", "lang": "en"})
    print(ltm.get("user_123", "profile"))

    print("---LRU裁剪---")
    tm = TruncatedMemory(max_length=3)
    for i in range(5):
        tm.add_message(f"msg_{i}")
    print(tm.get_history())

    print("---混合记忆---")
    hm = HybridMemory(max_short=2)
    hm.add_message("user_abc", "last_msg", "User: Hi!")
    hm.add_message("user_abc", "last_msg", "AI: Hello!")
    hm.add_message("user_abc", "last_msg", "User: How are you?")
    print(hm.get_short_history())
    print(hm.get_long_history("user_abc", "last_msg"))

# 你可以根据实际业务需求，扩展 Memory 结构，实现更复杂的记忆管理策略。