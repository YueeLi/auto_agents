# -*- coding: utf-8 -*-
import logging
from typing import Annotated
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

logger = logging.getLogger(__name__)


def create_python_repl_tool(**kwargs):
    """Creates a Python REPL tool instance."""
    repl = PythonREPL(**kwargs)

    @tool(description="Execute Python code and return the result.")
    def python_repl_tool(
        code: Annotated[
            str, "The python code to execute to do further analysis or calculation."
        ],
    ):
        """Use this to execute python code and do data analysis or calculation. If you want to see the output of a value,
        you should print it out with `print(...)`. This is visible to the user."""
        if not isinstance(code, str):
            error_msg = f"Invalid input: code must be a string, got {type(code)}"
            logger.error(error_msg)
            return f"Error executing code:\n```python\n{code}\n```\nError: {error_msg}"

        logger.info("Executing Python code")
        try:
            result = repl.run(code)
            if isinstance(result, str) and ("Error" in result or "Exception" in result):
                logger.error(result)
                return f"Error executing code:\n```python\n{code}\n```\nError: {result}"
            logger.info("Code execution successful")
        except BaseException as e:
            error_msg = repr(e)
            logger.error(error_msg)
            return f"Error executing code:\n```python\n{code}\n```\nError: {error_msg}"

        return f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"

    return python_repl_tool


# Example usage of the Python REPL tool
if __name__ == "__main__":
    example_code = "print('Hello, World!')"
    repl_tool = create_python_repl_tool()
    result = repl_tool.invoke(example_code)
    print(result)
