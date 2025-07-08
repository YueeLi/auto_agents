# -*- coding: utf-8 -*-
import logging
import json
from typing import Annotated, Dict, Any

from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL

logger = logging.getLogger(__name__)

# A global REPL instance maintains state between calls. 
# This can be useful for sequential operations but means executions are not isolated.
repl = PythonREPL()

@tool(description="Execute Python code and return the result as a JSON string.")
def python_repl_tool(
    code: Annotated[
        str, "The python code to execute to do further analysis or calculation."
    ],
) -> str:
    """
    Executes Python code in a REPL environment and returns the result as a JSON string.

    This tool captures stdout and returns it along with success status and any errors.
    It's designed for safe execution and structured output.

    Args:
        code: A string containing the Python code to be executed.

    Returns:
        A JSON string representing a dictionary with the following keys:
        - 'success' (bool): True if the code executed without errors, False otherwise.
        - 'code' (str): The input code that was executed.
        - 'stdout' (str): The standard output from the executed code.
        - 'error' (str): Any error message produced, or an empty string if successful.
    """
    if not isinstance(code, str):
        error_msg = f"Invalid input: code must be a string, but got {type(code).__name__}."
        logger.error(error_msg)
        result: Dict[str, Any] = {"success": False, "code": str(code), "stdout": "", "error": error_msg}
        return json.dumps(result)

    logger.info(f"Executing Python code:\n---\n{code}\n---")
    try:
        result_output = repl.run(code)
        
        # The `run` method of PythonREPL can return a string containing an error message.
        # Note: This check is a heuristic. It might misclassify successful outputs that contain the word "Error".
        if isinstance(result_output, str) and ("Error" in result_output or "Traceback" in result_output):
            logger.error(f"Execution failed with error: {result_output}")
            result = {"success": False, "code": code, "stdout": "", "error": result_output}
        else:
            logger.info("Code execution successful.")
            result = {"success": True, "code": code, "stdout": result_output, "error": ""}

    except Exception as e:
        error_msg = f"An unexpected exception occurred: {repr(e)}"
        logger.error(error_msg, exc_info=True)
        result = {"success": False, "code": code, "stdout": "", "error": error_msg}

    return json.dumps(result)


# Example usage of the Python REPL tool
if __name__ == "__main__":
    # Example of a successful execution
    success_code = "a = 5\nb = 10\nprint(f'The sum is {a + b}')"
    print("--- Testing successful execution ---")
    result_json_success = python_repl_tool.invoke({"code": success_code})
    print(json.dumps(json.loads(result_json_success), indent=2))

    # Example of an execution with a syntax error
    error_code = "print(undefined_variable)"
    print("\n--- Testing execution with an error ---")
    result_json_error = python_repl_tool.invoke({"code": error_code})
    print(json.dumps(json.loads(result_json_error), indent=2))
