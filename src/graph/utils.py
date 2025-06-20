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



