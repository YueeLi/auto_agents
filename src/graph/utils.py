from langgraph.graph.graph import CompiledGraph
from IPython.display import Image, display


def build_image(graph: CompiledGraph):
    """
    构建 StateGraph 的图像表示。
    """
    # 使用 graphviz 绘制图像
    # 图像存储在当前目录下的 images 文件夹中
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(current_dir, "images")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    # 图像文件名为 类名_image.png
    image_name = f"{graph.name}_image.png"
    image_path = os.path.join(images_dir, image_name)
    print(f"创建图像: {image_path}")
    # 创建图像
    try:
        display(Image(graph.get_graph().draw_mermaid_png(output_file_path=image_path)))
    except Exception as e:
        print(f"创建图像时发生错误: {e}")


def add_human_in_the_loop(
    tool: Callable | BaseTool,
    *,
    interrupt_config: HumanInterruptConfig = None,
) -> BaseTool:
    """Wrap a tool to support human-in-the-loop review.""" 
    if not isinstance(tool, BaseTool):
        tool = create_tool(tool)

    if interrupt_config is None:
        interrupt_config = {
            "allow_ignore": False,
            "allow_accept": True,
            "allow_edit": True,
            "allow_respond": True,
        }

    @create_tool(  
        tool.name,
        description=tool.description,
        args_schema=tool.args_schema
    )
    def call_tool_with_interrupt(config: RunnableConfig, **tool_input):
        request: HumanInterrupt = {
            "action_request": {
                "action": tool.name,
                "args": tool_input
            },
            "config": interrupt_config,
            "description": "Please review the tool call"
        }
        response = interrupt([request])[0]  
        # approve the tool call
        if response["type"] == "accept":
            tool_response = tool.invoke(tool_input, config)
        # update tool call args
        elif response["type"] == "edit":
            tool_input = response["args"]["args"]
            tool_response = tool.invoke(tool_input, config)
        # respond to the LLM with user feedback
        elif response["type"] == "response":
            user_feedback = response["args"]
            tool_response = user_feedback
        else:
            raise ValueError(f"Unsupported interrupt response type: {response['type']}")

        return tool_response

    return call_tool_with_interrupt
