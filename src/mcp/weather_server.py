from mcp.server.fastmcp import FastMCP
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import (
    Connection,
    McpHttpClientFactory,
    SSEConnection,
    StdioConnection,
    StreamableHttpConnection,
    WebsocketConnection,
    create_session,
)



weather = FastMCP("weather")

@weather.tool("get_weather")
def get_weather(city: str) -> str:
    """
    获取指定城市的天气信息
    :param city: 城市名称
    :return: 天气信息字符串
    """
    # 这里可以调用实际的天气API或数据库查询
    # 目前返回一个模拟的天气信息
    return f"The weather in {city} is sunny with a temperature of 25°C."


@weather.tool("get_forecast")
def get_forecast(city: str, days: int = 3) -> str:
    """
    获取指定城市的天气预报
    :param city: 城市名称
    :param days: 预报天数，默认为3天
    :return: 天气预报信息字符串
    """
    # 这里可以调用实际的天气API或数据库查询
    # 目前返回一个模拟的天气预报信息
    return f"The weather forecast for {city} for the next {days} days is sunny with temperatures around 25°C."




client = MultiServerMCPClient(
            {
                "math": {
                    "command": "python",
                    # Make sure to update to the full absolute path to your math_server.py file
                    "args": ["/path/to/math_server.py"],
                    "transport": "stdio",
                },
                "weather": {
                    # make sure you start your weather server on port 8000
                    "url": "http://localhost:8000/mcp",
                    "transport": "streamable_http",
                }
            }
        )

tools = await client.get_tools()