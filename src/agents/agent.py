from langgraph.prebuilt import create_react_agent
from src.config import LLMType
from src.llms import get_llm_by_type
from src.prompt import get_prompt_template # Import get_prompt_template
# from langgraph_supervisor import create_supervisor # This seems unused for single agent

# Create different types of agents using the React framework
def create_agent(tools: list, llm_type: LLMType, template_name: str):
    return create_react_agent(
        model=get_llm_by_type(llm_type),
        tools=tools,
        prompt=get_prompt_template(template_name)
    )


