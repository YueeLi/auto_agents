"""
LangGraph State 全面知识点与实战演示
=====================================================

## 关键要点梳理

### 核心概念
1. **状态定义**：使用 `TypedDict` 定义图状态结构，支持类型注解和验证 [1](#0-0) 
2. **状态更新**：通过节点返回值或 `Command(update=...)` 更新状态 [2](#0-1) 
3. **状态持久化**：依赖 checkpointer 在每个超级步骤后保存状态快照 [3](#0-2) 

### 状态管理机制
4. **Reducer 函数**：使用 `Annotated` 类型定义状态字段的合并策略 [4](#0-3) 
5. **状态快照**：`StateSnapshot` 对象包含状态值、配置、元数据和下一步任务 [5](#0-4) 
6. **跨节点共享**：状态在所有节点间共享，支持部分更新和增量修改

### 高级特性
7. **状态检索**：通过 `get_state()` 方法获取当前或历史状态 [5](#0-4) 
8. **状态回滚**：支持时间旅行功能，可回到任意历史状态点
9. **子图状态**：子图可以有独立的状态模式，支持状态映射和转换 [6](#0-5) 

### 执行机制
10. **状态传递**：节点函数接收当前状态作为参数，返回状态更新
11. **状态合并**：使用 reducer 函数处理并发更新和状态冲突
12. **状态验证**：支持运行时状态类型检查和结构验证

## 核心概念详解

### 1. 状态定义：TypedDict 结构化状态

LangGraph 使用 `TypedDict` 作为状态模式的基础，这在 [1](#1-0)  中有详细说明。状态定义的核心在于：

**基础状态结构**： [2](#1-1) 

**多模式状态支持**：
- `TypedDict`：最常用的状态定义方式
- `Pydantic BaseModel`：支持数据验证和默认值
- `dataclass`：轻量级的状态结构

**状态字段类型**：
- 简单类型：`str`, `int`, `bool`
- 复合类型：`list`, `dict`, 自定义对象
- 带 reducer 的注解类型：`Annotated[list[str], add]`

### 2. 状态更新机制：节点返回值处理

状态更新遵循严格的合并规则，如 [3](#1-2)  中 `StateGraph` 类的实现所示：

**节点返回值处理**：
- 节点 (Node) 函数不应直接修改传入的状态对象
- 节点函数返回字典形式的状态更新
- 只需返回需要更新的字段，不必返回完整状态
- 返回值会与当前状态合并，而非替换

```
def my_node(state: AgentState) -> dict:
    # 错误的做法: state['new_key'] = 'value'
    # 正确的做法: 返回一个包含更新的字典
    return {"plan": "A new plan...", "next_node": "action"}
```

**Command 更新方式**： [4](#1-3) 
这种更新方式允许同时进行状态更新和控制流跳转。

```python
def my_node(state: State) -> Command[Literal["other_subgraph"]]:
    return Command(
        update={"foo": "bar"},
        goto="other_subgraph",  # where `other_subgraph` is a node in the parent graph
        graph=Command.PARENT
    )
```

### 3. 状态持久化：Checkpoint 深度机制

状态持久化通过 checkpointer 实现，每个超级步骤后自动保存状态快照：

**StateSnapshot 结构**： [5](#1-4) 

**持久化时机**：
- 每个节点执行完成后
- 图执行中断时
- 人工干预点
- 错误发生时

## 状态管理机制详解

### 4. Reducer 函数：状态合并的核心逻辑

Reducer 函数决定了多个状态更新如何合并，这是 LangGraph 状态管理的关键机制：

**内置 Reducer**： [6](#1-5) 

**Reducer 工作原理**：
- 当多个节点同时更新同一字段时触发
- 按照定义的 reducer 函数合并值
- 确保状态更新的一致性和可预测性

**常用 Reducer 模式**：
- `operator.add`：数值相加、列表合并
- `operator.or_`：字典合并
- 自定义函数：复杂业务逻辑合并

### 5. 状态快照：完整的执行上下文

StateSnapshot 不仅包含状态值，还包含完整的执行上下文，这使得时间旅行和状态恢复成为可能。

### 6. 跨节点状态共享：全局访问模式

所有节点都可以访问完整的图状态，但只能通过返回值更新状态，这确保了状态变更的可追踪性。

## 高级特性详解

### 7. 状态检索：get_state() 深度应用

状态检索不仅可以获取当前状态，还支持历史状态查询和条件过滤。

```
snapshot = graph.get_state(config)  
current_values = snapshot.values
```

### 8. 状态回滚：时间旅行的技术实现

时间旅行功能基于 checkpoint 机制,支持回到任意历史状态点：

- 查看历史状态快照
- 从特定点重新开始执行
- 探索不同的执行路径

### 9. 子图状态：层次化状态管理

子图状态管理涉及状态映射和转换，特别是在多代理系统中： [7](#1-6) 

这要求在父图中定义适当的 reducer 来处理子图的状态更新。

## 执行机制详解

### 10. 状态传递：函数签名和参数处理

节点函数的标准模式是接收状态作为第一个参数，返回状态更新字典。
```
def node_function(state: State) -> dict:  
    # 访问当前状态  
    current_value = state["key"]  
    # 返回状态更新  
    return {"key": "new_value"}
```

### 11. 状态合并：并发更新的处理策略

当多个节点并发执行时，LangGraph 使用 reducer 函数确保状态合并的确定性。

### 12. 状态验证：运行时类型检查

LangGraph 在运行时验证状态更新是否符合定义的模式，确保类型安全。

## 实际应用场景详解

### Human-in-the-Loop 中的状态管理

在人工干预场景中，状态用于保存中断上下文： [8](#1-7) 

```python
def human_editing(state: State):
    ...
    result = interrupt(
        # Interrupt information to surface to the client.
        # Can be any JSON serializable value.
        {
            "task": "Review the output from the LLM and make any necessary edits.",
            "llm_generated_summary": state["llm_generated_summary"]
        }
    )

    # Update the state with the edited text
    return {
        "llm_generated_summary": result["edited_text"] 
    }
```

这个例子展示了如何在 `interrupt()` 调用中传递状态信息，以及如何处理人工输入的结果。

### 多代理系统中的状态协调

在多代理架构中，状态管理涉及：
- 全局状态的共享访问
- 代理间的状态隔离
- 状态冲突的解决机制

## Notes

状态管理是 LangGraph 的核心功能，与持久化、人工干预、多代理协作等特性紧密集成。理解状态的定义、更新、持久化和检索机制对于构建复杂的图应用至关重要。特别需要注意 reducer 函数的使用，它决定了状态合并的行为，在并发更新和子图交互中尤为重要。

Wiki pages you might want to explore:
- [Human-in-the-Loop Capabilities (langchain-ai/langgraph)](/wiki/langchain-ai/langgraph#4)
"""

# 1. State 的基本定义与作用
# State 是 LangGraph 中用于在节点间传递和存储信息的核心结构，相当于“全局上下文”或“记忆体”。

# 2. 基础 State 结构（如计数器）
from typing import TypedDict

class BasicState(TypedDict):
    count: int  # 用于记录计数、轮次等简单信息

# 示例：初始化与简单修改
basic_state: BasicState = {"count": 0}
def increment_count(state: BasicState) -> BasicState:
    """返回一个新的 state，count +1，体现不可变性原则"""
    return {"count": state["count"] + 1}

# 3. 复杂 State 结构（如消息历史、嵌套结构、TypedDict/Dataclass）
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ConversationMemory:
    short_term: List[str]
    long_term: Dict[str, Any]
    metadata: Dict[str, Any]

class AdvancedState(TypedDict):
    messages: List[str]
    memory: ConversationMemory
    context: Dict[str, Any]
    metrics: Dict[str, float]

def create_advanced_state() -> AdvancedState:
    return {
        "messages": [],
        "memory": ConversationMemory(short_term=[], long_term={}, metadata={}),
        "context": {},
        "metrics": {"confidence": 0.0, "relevance": 0.0}
    }

# 4. State 的不可变性与修改方式
# 推荐每次都返回新对象，避免副作用

def add_message(state: AdvancedState, message: str) -> AdvancedState:
    """添加消息，返回新 state"""
    new_messages = state["messages"] + [message]
    return {**state, "messages": new_messages}

# 5. State 的类型注解与校验

def validate_state_transition(current_state: AdvancedState, new_state: AdvancedState) -> bool:
    """校验状态变迁，保证一致性和安全性"""
    if len(new_state["messages"]) < len(current_state["messages"]):
        return False
    if new_state["metrics"]["confidence"] < 0 or new_state["metrics"]["confidence"] > 1:
        return False
    return True

def safe_state_transition(current_state: AdvancedState, update_func) -> AdvancedState:
    """安全地应用状态变迁"""
    new_state = update_func(current_state)
    if not validate_state_transition(current_state, new_state):
        raise ValueError("Invalid state transition")
    return new_state

# 6. State 的手动与自动更新
# 手动：如上通过函数显式更新
# 自动：结合 Graph 节点自动传递和变更

# 7. State 在节点间传递与分支（Conditional Branching）
# 伪代码示例：
def should_continue(state: AdvancedState) -> bool:
    """根据 state 条件决定流程分支"""
    return state["metrics"]["confidence"] < 0.8

# 8. State 的高级用法
# - 多层嵌套/多类型数据
# - 结合 Memory、Context、Metrics
# - 状态变迁校验与安全更新（见上）

# 9. State 与 Graph 结合的典型场景
# 伪代码：
# from langgraph.graph import StateGraph, END
# workflow = StateGraph(AdvancedState)
# def node_fn(state: AdvancedState):
#     ... # 处理 state
#     return new_state
# workflow.add_node("process", node_fn)
# workflow.set_entry_point("process")
# workflow.add_edge("process", END)
# graph = workflow.compile()

# 10. State 的调试、断点与时光回溯（Time Travel）
# - 可用断点/日志/回溯工具分析 state 变化
# - 伪代码：
# class GraphDebugger:
#     def log_state(self, state, node, event): ...
#     def print_execution_path(self): ...
#     def analyze_state_changes(self): ...

# 11. 常见陷阱与最佳实践
# - 避免直接修改 state，始终返回新对象
# - 类型注解要准确，便于调试和维护
# - 节点内异常要捕获，避免影响全局 state
# - 复杂流程建议拆分 state 结构，便于扩展

# 结语：
# 掌握 state 的设计与用法，是构建强大 LangGraph 工作流的基础。
# 更多高级特性可结合官方文档与社区实践持续探索。
