"""
This package aggregates all the tools from the different modules within this directory.

The goal is to provide a single, unified list of tools that can be easily imported
and used by the agent creation logic.

By using an `__all__` declaration, we explicitly define the public API of this package,
making it clear which names are intended for external use.
"""

from src.tools.builtin import all_tools as builtin_tools
from src.tools.python_repl import python_repl_tool
from src.tools.web_crawl import tavily_web_crawl, playwright_web_crawl

# Combine all tools from the different modules into a single list.
# This list serves as the central point of access for all available tools.
all_tools = builtin_tools + [python_repl_tool, tavily_web_crawl, playwright_web_crawl]

# Define the public API of the 'tools' package.
# When another module executes `from src.tools import *`, only 'all_tools' will be imported.
__all__ = ["all_tools"]