"""
LangGraph Graph 全面知识点与实战演示
=====================================================

## 关键要点梳理

### 核心概念
1. **图定义**：使用 `StateGraph` 类定义图结构，支持状态驱动的工作流 [1](#0-0) 
2. **节点系统**：Python 函数作为节点，接收状态并返回状态更新 [2](#0-1) 
3. **边连接**：Python 函数决定下一个执行的节点，支持条件分支 [3](#0-2) 

### 执行机制
4. **超级步骤**：基于 Pregel 系统的消息传递模型，离散执行步骤 [4](#0-3) 
5. **图编译**：通过 `.compile()` 方法编译图，进行结构检查和运行时配置 [5](#0-4) 
6. **并行执行**：同一超级步骤内的节点并行执行，顺序节点属于不同超级步骤 [6](#0-5) 

### 控制流特性
7. **条件边**：基于状态动态路由到不同节点 [7](#0-6) 
8. **Send API**：支持 map-reduce 模式，动态创建多个并行任务 [8](#0-7) 
9. **Command API**：结合状态更新和控制流跳转 [9](#0-8) 

### 高级架构
10. **子图系统**：图作为节点嵌入其他图，支持复杂系统构建 [10](#0-9) 
11. **多代理架构**：通过子图和 Command 实现代理间通信 [11](#0-10) 
12. **人机交互**：支持中断和恢复机制，实现人工干预工作流 [12](#0-11) 

## 核心概念详解

### 1. 图定义：StateGraph 架构基础

LangGraph 的核心是 `StateGraph` 类，它定义了状态驱动的图结构 [13](#0-12) ：

**图初始化模式**：
- 状态模式定义：支持 `TypedDict`、`Pydantic BaseModel`、`dataclass`
- 配置模式：可选的运行时配置参数定义
- 输入输出模式：支持不同的输入输出结构

**基础图构建流程** [14](#0-13) ：
```python
graph_builder = StateGraph(State)
```

### 2. 节点系统：计算单元的核心

节点是图中的计算单元，通常是 Python 函数 [15](#0-14) ：

**节点函数签名**：
- 第一个参数：当前状态
- 第二个参数（可选）：配置信息
- 返回值：状态更新字典

**节点添加方式** [16](#0-15) ：
- 显式命名：`builder.add_node("node_name", function)`
- 自动命名：`builder.add_node(function)` 使用函数名

### 3. 边连接：控制流的实现

边决定了图的执行流程，支持多种连接模式：

**固定边**：直接连接两个节点 [17](#0-16) 

**条件边**：基于状态动态路由 [18](#0-17) 

**入口点配置**：从虚拟 START 节点开始 [17](#0-16) 

## 执行机制详解

### 4. 超级步骤：Pregel 消息传递模型

LangGraph 基于 Google Pregel 系统实现消息传递 [4](#0-3) ：

**执行模型特点**：
- 离散的超级步骤执行
- 并行节点在同一超级步骤内执行
- 顺序节点属于不同超级步骤
- 节点状态：`inactive` → `active` → `inactive`

**终止条件**：所有节点处于 `inactive` 状态且无消息传输时终止

### 5. 图编译：结构验证与配置

编译是图执行前的必要步骤 [5](#0-4) ：

**编译功能**：
- 图结构验证（无孤立节点等）
- 运行时参数配置（checkpointer、断点等）
- 生成可执行的图对象

**编译配置选项**：
- `checkpointer`：状态持久化
- `interrupt_before_nodes`：节点前断点
- `interrupt_after_nodes`：节点后断点

### 6. 并行执行：性能优化机制

图支持节点的并行执行以提高性能 [19](#0-18) ：

**并行执行特点**：
- 同一超级步骤内的节点并行执行
- 事务性：任一节点失败则整个超级步骤失败
- 使用 checkpointer 时成功节点的结果会保存

## 控制流特性详解

### 7. 条件边：动态路由实现

条件边允许基于状态动态决定下一个执行节点 [18](#0-17) ：

**路由函数特点**：
- 接收当前状态作为参数
- 返回值作为目标节点名称
- 支持字典映射返回值到节点名称

### 8. Send API：Map-Reduce 模式支持

Send API 支持动态创建多个并行任务 [20](#0-19) ：

**使用场景**：
- 边数量未知的情况
- 需要不同状态版本的并行处理
- Map-reduce 设计模式

**Send 对象结构**：
- 第一个参数：目标节点名称
- 第二个参数：传递给节点的状态

### 9. Command API：状态更新与控制流结合

Command API 允许在单个节点中同时进行状态更新和控制流跳转 [9](#0-8) ：

**Command 对象属性**：
- `update`：状态更新字典
- `goto`：目标节点名称
- `graph`：目标图（支持父图导航）

**使用场景**：多代理切换、动态控制流、状态传递

## 高级架构详解

### 10. 子图系统：层次化图结构

子图允许将图作为节点嵌入其他图中 [10](#0-9) ：

**子图通信模式**：
- **共享状态模式**：父图和子图共享状态键 [21](#0-20) 
- **不同状态模式**：需要状态转换函数 [22](#0-21) 

**应用场景**：
- 多代理系统构建
- 代码复用和模块化
- 团队协作开发

### 11. 多代理架构：Agent 间协调

多代理系统通过子图和 Command 实现代理间通信 [23](#0-22) ：

**Handoff 机制**：
- 目标代理指定
- 状态信息传递
- 跨图导航支持

**架构模式**：
- 监督者模式
- 层次化架构
- 自定义工作流

### 12. 人机交互：中断与恢复机制

图支持人工干预工作流 [24](#0-23) ：

**中断机制**：
- 动态中断：`interrupt()` 函数
- 静态断点：编译时配置
- 状态保存：依赖 checkpointer

**恢复机制**：
- Command 对象恢复
- 状态更新和继续执行
- 支持多轮交互

## 实际应用场景详解

### 基础聊天机器人构建

使用 StateGraph 构建简单聊天机器人 [25](#0-24) ：

**核心组件**：
- 状态定义：消息列表管理
- 节点函数：LLM 调用逻辑
- 边连接：简单的线性流程

### 复杂工作流编排

支持复杂的业务逻辑编排 [26](#0-25) ：

**工作流特点**：
- 多步骤处理
- 条件分支
- 状态累积更新

### 多代理协作系统

实现多个 AI 代理的协作 [27](#0-26) ：

**系统特点**：
- 代理间状态共享
- 动态任务分配
- 层次化管理结构

## Notes

Graph 概念是 LangGraph 的核心抽象，它将复杂的 AI 工作流建模为状态驱动的有向图。与传统的函数调用链不同，LangGraph 的图模型支持并行执行、条件分支、状态持久化和人工干预等高级特性。通过 StateGraph 类、节点函数、边连接和各种控制流 API，开发者可以构建从简单聊天机器人到复杂多代理系统的各种应用。图的编译和执行机制基于 Google Pregel 系统，确保了高效的并行处理和可靠的状态管理。

Wiki pages you might want to explore:
- [Human-in-the-Loop Capabilities (langchain-ai/langgraph)](/wiki/langchain-ai/langgraph#4)
- [Persistence System (langchain-ai/langgraph)](/wiki/langchain-ai/langgraph#5)
"""


################################################################################
#
# 实战演示：构建一个覆盖核心知识点的复杂 LangGraph 图
#
# 本示例将构建一个“多智能体研究团队”工作流，旨在演示 LangGraph 的核心功能。
# 这个团队由一个“规划师”和多个并行的“研究员”以及一个“报告撰写者”组成。
#
# 覆盖的知识点（对应文件顶部的注释编号）：
# 1. 图定义 (StateGraph)
# 2. 节点系统 (Python 函数)
# 3. 边连接 (固定边 & 条件边)
# 5. 图编译 (compile)
# 6. 并行执行 (通过 Send API 实现)
# 7. 条件边 (Conditional Edges)
# 8. Send API (用于 Map-Reduce 模式)
# 11. 多代理架构 (通过不同角色的节点模拟)
# 12. 人机交互 (中断与恢复)
#
################################################################################

import asyncio
from typing import TypedDict, List, Dict

from langgraph.checkpoint.aiosqlite import AsyncSqliteSaver
from langgraph.graph import StateGraph, END, Send
from langgraph.graph.message import add_messages


# 为了使示例可独立运行，我们使用 mock 函数模拟 LLM 调用
def mock_planner_llm(topic: str) -> List[str]:
    """模拟规划师 LLM，将主题分解为子任务。"""
    print(f"--- 规划师正在为主题 '{topic}' 生成研究计划... ---")
    return [
        f"探究 {topic} 的历史渊源",
        f"分析 {topic} 的当前市场现状",
        f"预测 {topic} 的未来发展趋势",
    ]


def mock_researcher_llm(query: str) -> str:
    """模拟研究员 LLM，针对子问题进行“研究”。"""
    print(f"--- 研究员正在研究: '{query}'... ---")
    # 模拟耗时操作
    asyncio.sleep(1)
    return f"关于 '{query}' 的详细研究报告内容..."


def mock_writer_llm(research_data: Dict) -> str:
    """模拟报告撰写者 LLM，将研究结果整合成最终报告。"""
    print("--- 报告撰写者正在整合所有研究资料，生成最终报告... ---")
    report_parts = ["# 最终研究报告\n\n"]
    for query, result in research_data.items():
        report_parts.append(f"## {query}\n\n{result}\n\n")
    return "".join(report_parts)


# [知识点 1] 图定义：使用 TypedDict 定义图的状态 (State)
class ResearchTeamState(TypedDict):
    """定义研究团队工作流的状态。"""
    topic: str
    sub_queries: List[str]
    # `add_messages` 是一种方便的 reducer，用于将并行研究员节点返回的结果聚合到一个列表中
    # 每个研究员返回一个字典 {'query': 'result'}，最终会形成一个字典列表
    research_results: Annotated[list[dict], add_messages]
    # 聚合后的研究数据
    aggregated_data: Dict[str, str]
    # 最终报告
    final_report: str
    # 用于人机交互的标志
    human_review_passed: bool


# [知识点 2] 节点系统：每个节点都是一个 Python 函数
def planner_node(state: ResearchTeamState):
    """规划师节点：接收主题，生成研究子查询。"""
    queries = mock_planner_llm(state["topic"])
    return {"sub_queries": queries}


async def researcher_node(state: ResearchTeamState):
    """研究员节点：接收一个子查询并返回研究结果。
    注意：此节点将由 Send API 并行调用。
    `state['sub_queries']` 此时是一个列表，但 `Send` 会为每个任务传入一个特定的子查询。
    """
    # `Send` 会将任务特定的值放入状态中，我们在这里读取它
    query = state["sub_queries"]
    result = await asyncio.to_thread(mock_researcher_llm, query)
    # 返回的结果将通过 `add_messages` 聚合到 `research_results` 列表中
    return {"research_results": [{query: result}]}


def aggregator_node(state: ResearchTeamState):
    """聚合节点：将并行研究的结果合并成一个字典。"""
    print("--- 聚合所有研究员的成果... ---")
    aggregated = {}
    for res_dict in state["research_results"]:
        aggregated.update(res_dict)
    return {"aggregated_data": aggregated}


def writer_node(state: ResearchTeamState):
    """报告撰写节点：生成最终报告。"""
    report = mock_writer_llm(state["aggregated_data"])
    return {"final_report": report}


def human_review_node(state: ResearchTeamState):
    """人机交互节点：此节点仅用于触发中断，让人类进行审核。"""
    print("--- 等待人工审核... ---")
    # 实际操作在中断和恢复逻辑中完成
    return {}


# [知识点 7 & 8] 条件边 & Send API
def router_function(state: ResearchTeamState):
    """路由函数：决定下一步是结束还是分发任务给研究员。"""
    print("--- 规划完成，准备分发研究任务... ---")
    # 使用 Send API 为每个子查询动态创建一个并行的 researcher_node 任务
    # 这是 Map-Reduce 模式的体现
    if not state["sub_queries"]:
        return END
    return [Send("researcher", {"sub_queries": q}) for q in state["sub_queries"]]


def after_review_router(state: ResearchTeamState):
    """审核后路由：根据人工审核结果决定是生成报告还是结束。"""
    print("--- 人工审核结束，进行路由... ---")
    if state.get("human_review_passed"):
        return "writer"
    else:
        print("--- 人工审核未通过，工作流结束。 ---")
        return END


# [知识点 1, 2, 3] 图构建：定义状态、添加节点和边
graph_builder = StateGraph(ResearchTeamState)

graph_builder.add_node("planner", planner_node)
graph_builder.add_node("researcher", researcher_node)
graph_builder.add_node("aggregator", aggregator_node)
graph_builder.add_node("human_review", human_review_node)
graph_builder.add_node("writer", writer_node)

graph_builder.set_entry_point("planner")

# [知识点 6 & 8] 从 planner 节点出来后，使用条件路由和 Send API 实现并行执行
graph_builder.add_conditional_edges("planner", router_function)

# [知识点 3] 所有并行的 researcher 节点完成后，结果会汇集到 aggregator 节点
graph_builder.add_edge("researcher", "aggregator")

# 聚合后进入人工审核环节
graph_builder.add_edge("aggregator", "human_review")

# [知识点 7] 根据人工审核结果，决定下一步走向
graph_builder.add_conditional_edges(
    "human_review",
    after_review_router,
    {"writer": "writer", END: END},
)

graph_builder.add_edge("writer", END)

# [知识点 5 & 12] 图编译与人机交互配置
# 使用内存中的 SQLite 作为检查点，以支持中断和恢复
memory_saver = AsyncSqliteSaver.new_memory()

research_graph = graph_builder.compile(
    checkpointer=memory_saver,
    # 在 `human_review` 节点之前中断，以实现人工干预
    interrupt_before=["human_review"],
)


async def main():
    """主函数：执行图并处理人机交互。"""
    config = {"configurable": {"thread_id": "research-thread-1"}}
    topic = "人工智能在软件工程中的应用"
    inputs = {"topic": topic}

    print(f"🚀 开始执行研究工作流，主题: {topic}")
    
    # 异步执行图
    async for event in research_graph.astream(inputs, config=config):
        for v in event.values():
            print(f"节点 '{next(iter(v))}' 已完成。")

    # [知识点 12] 处理中断
    # 此时图的执行已在 `human_review` 节点前暂停
    snapshot = await research_graph.aget_state(config)
    print("\n⏸️ 工作流已中断，等待人工审核。")
    print("当前研究成果:")
    print(snapshot.values["aggregated_data"])

    # 模拟人工审核过程
    user_input = input("研究成果是否通过审核？(yes/no): ").strip().lower()
    
    if user_input == 'yes':
        print("✅ 审核通过，继续执行以生成最终报告...")
        # 更新状态并恢复执行
        await research_graph.aupdate_state(
            config, {"human_review_passed": True}
        )
        # 从中断处继续执行
        async for event in research_graph.astream(None, config=config):
             for v in event.values():
                print(f"节点 '{next(iter(v))}' 已完成。")
    else:
        print("❌ 审核未通过，工作流将终止。")
        await research_graph.aupdate_state(
            config, {"human_review_passed": False}
        )
        async for event in research_graph.astream(None, config=config):
             for v in event.values():
                print(f"节点 '{next(iter(v))}' 已完成。")

    # 打印最终状态
    final_state = await research_graph.aget_state(config)
    if final_state.values.get("final_report"):
        print("\n📄 === 最终报告 ===\n")
        print(final_state.values["final_report"])
    else:
        print("\n工作流已结束，未生成最终报告。")


if __name__ == "__main__":
    # 在 Python 3.8+ 中，可以直接运行 async main
    asyncio.run(main())
