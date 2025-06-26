"""
LangGraph Human-in-the-Loop (HITL) 全面知识点与实战演示
=====================================================

本文件系统性演示 LangGraph human-in-the-loop 的所有核心特性、用法、技巧与注意事项。

## 关键要点梳理

### 核心机制
1. **基本用法**：`interrupt()` + `Command(resume=...)` 实现暂停与恢复
2. **中断类型**：动态中断（函数调用）vs 断点中断（编译时配置）
3. **持久化要求**：必须配置 checkpointer 和 thread_id

### 交互模式
4. **审批模式**：Approve/Reject 实现分支跳转
5. **编辑模式**：修改 State 或 LLM 输出
6. **工具调用审核**：审核/修改工具调用参数
7. **多轮输入校验**：同一节点内多次中断验证

### 高级特性
8. **批量恢复**：使用映射字典一次恢复多个中断
9. **命名空间追踪**：精确定位嵌套结构中的中断位置
10. **可恢复性控制**：通过 `resumable` 字段控制恢复行为

### 执行机制与陷阱
11. **恢复机制**：节点从头重新执行，非断点续行
12. **顺序依赖**：多 interrupt 时严格按索引顺序匹配
13. **子图行为**：子图中断的特殊恢复逻辑
14. **副作用处理**：副作用代码必须放在 interrupt 之后

### 最佳实践
15. **UI 集成**：与 Agent Inbox 等界面的标准化集成
16. **错误处理**：中断验证和异常处理机制
17. **性能优化**：避免重复执行和状态冲突

## 核心机制详解

### 1. 基本用法：interrupt + Command 实现暂停与恢复 [1](#1-0) 

`interrupt()` 函数是 HIL 的核心机制。当在节点内调用时，它会抛出 `GraphInterrupt` 异常来暂停执行，并将提供的值发送给客户端。客户端必须使用 `Command(resume=...)` 来提供恢复值并继续执行。 [2](#1-1) 

关键特点：
- 节点会从头重新执行，而不是从中断点继续
- 需要配置 checkpointer 来持久化状态
- 必须提供 thread_id 来维护会话连续性

### 2. 中断类型：动态中断 vs 断点中断

**动态中断**通过在节点函数内调用 `interrupt()` 触发，允许基于运行时条件决定是否中断。

**断点中断**在编译时通过 `interrupt_before_nodes` 和 `interrupt_after_nodes` 配置，会在指定节点前后自动暂停执行。

### 3. 持久化要求：checkpointer 和 thread_id [3](#1-2) 

HIL 功能依赖于持久化机制：
- **Checkpointer**：保存图状态，支持 `InMemorySaver`（开发）、`PostgresSaver`（生产）等
- **Thread ID**：标识会话，确保中断和恢复操作在正确的上下文中进行

## 交互模式详解

### 4. 审批模式：Approve/Reject 实现分支跳转 [4](#1-3) 

审批模式允许人工决定执行路径。节点可以返回 `Command(goto="node_name")` 来实现条件分支，根据人工输入决定下一步执行哪个节点。

### 5. 编辑模式：修改 State 或 LLM 输出

人工可以直接修改图的状态或 LLM 的输出。通过 `Command(update={"key": "new_value"})` 来更新状态，然后继续执行。

### 6. 工具调用审核：审核/修改工具调用参数 [5](#1-4) 

LangGraph 提供了 `add_human_in_the_loop()` 包装器，可以为任何工具添加人工审核功能。支持三种操作：
- **accept**：批准工具调用
- **edit**：修改工具参数
- **response**：提供自定义响应

### 7. 多轮输入校验：同一节点内多次中断验证 [6](#1-5) 

同一节点可以包含多个 `interrupt()` 调用，用于多轮验证。LangGraph 维护每个任务的恢复值列表，按索引严格匹配。

## 高级特性详解

### 8. 批量恢复：使用映射字典一次恢复多个中断 [7](#1-6) 

当有多个中断在任务队列中时，可以使用字典映射一次性恢复所有中断：
```python
resume_map = {
    i.interrupt_id: f"human input for prompt {i.value}"
    for i in parent.get_state(thread_config).interrupts
}
```

### 9. 命名空间追踪：精确定位嵌套结构中的中断位置 [8](#1-7) 

每个中断都有命名空间序列 (`ns`) 来标识其在图结构中的位置。`interrupt_id` 通过对命名空间进行哈希生成唯一标识符，用于在嵌套图和子图中精确定位中断。

### 10. 可恢复性控制：resumable 字段 [9](#1-8) 

`Interrupt` 对象的 `resumable` 字段控制中断是否可以恢复。默认为 `False`，需要显式设置为 `True` 才能通过 `Command(resume=...)` 恢复执行。

## 执行机制与陷阱详解

### 11. 恢复机制：节点从头重新执行 [10](#1-9) 

这是最重要的陷阱：恢复时节点会从头开始执行，不是从中断点继续。所有在 `interrupt()` 之前的代码都会重新运行，包括副作用操作。

### 12. 顺序依赖：多 interrupt 时严格按索引顺序匹配 [11](#1-10) 

多个中断的匹配是严格按索引顺序的，不能动态改变节点结构（添加、删除或重排中断调用），否则会导致索引错位。

### 13. 副作用处理：必须放在 interrupt 之后 [12](#1-11) 

所有有副作用的代码（如 API 调用、数据库写入）必须放在 `interrupt()` 之后，避免在节点重新执行时重复触发。

## 最佳实践详解

### 15. UI 集成：与 Agent Inbox 等界面的标准化集成 [13](#1-12) 

LangGraph 提供了与 Agent Inbox UI 和 Agent Chat UI 兼容的标准化包装器，支持配置化的交互选项（允许接受、编辑、响应等）。

### 16. 错误处理和验证机制

系统包含多层验证：
- Thread ID 和 checkpointer 的存在性检查
- 中断可恢复性验证
- 命名空间有效性检查
- 恢复值类型和格式验证

### 17. 性能优化考虑

- 避免在中断前执行昂贵操作
- 合理设计节点粒度，减少重复执行开销
- 使用适当的 checkpointer 实现（生产环境使用数据库后端）
- 考虑中断频率对整体性能的影响

"""


from hmac import new
from typing import Literal, final
from langgraph.types import Command,interrupt
from langchain_core.messages import HumanMessage
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.graph import MessagesState
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
