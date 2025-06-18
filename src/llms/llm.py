# Create llm by configuration

from src.config import load_yaml_config
from src.config import LLMType
from typing import Dict, Any
from pathlib import Path

from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_openai.chat_models.base import BaseChatOpenAI



_llm_cache: dict[LLMType, BaseChatOpenAI] = {}


def _create_llm_by_config(llm_type: LLMType, conf: Dict[str, Any]) -> BaseChatOpenAI:
    """
    Create an LLM instance based on the provided configuration.
    Args:
        llm_type (LLMType): The type of LLM to create.
        conf (Dict[str, Any]): Configuration dictionary containing LLM settings.
    Returns:
        ChatOpenAI: An instance of the specified LLM type.
    Raises:
        ValueError: If the LLM type is unsupported or the configuration is invalid.
    """
    llm_type_mapping = {
        "basic": conf.get("BASIC_MODEL"),
        "reasoning": conf.get("REASONING_MODEL"),
        "vision": conf.get("VISION_MODEL")
    }
    llm_config = llm_type_mapping.get(llm_type)
    if not llm_config:
        raise ValueError(f"Unsupported LLM type: {llm_type}")
    if not isinstance(llm_config, dict):
        raise ValueError(f"Invalid configuration for LLM type {llm_type}: {llm_config}")
    # 如果配置中存在 azure_endpoint 字段，则创建 AzureChatOpenAI 实例
    if "azure_endpoint" in llm_config:
        return AzureChatOpenAI(**llm_config)
    # 否则创建 ChatOpenAI 实例
    return ChatOpenAI(**llm_config)
    

def get_llm_by_type(llm_type: LLMType) -> BaseChatOpenAI:
    """
    Get an LLM instance by its bype, return cached instance if available.
    Args:
        llm_type (LLMType): The type of LLM to retrieve.
    Returns:
        ChatOpenAI: An instance of the specified LLM type.
    Raises:
        ValueError: If the LLM type is unsupported.
    """
    if llm_type not in _llm_cache:
        conf = load_yaml_config(
            str((Path(__file__).parent.parent.parent / "conf.yaml").resolve())
        )
        _llm_cache[llm_type] = _create_llm_by_config(llm_type, conf)
    return _llm_cache[llm_type]


basic_llm = get_llm_by_type("basic")
reasoning_llm = get_llm_by_type("reasoning")
vision_llm = get_llm_by_type("vision")


if __name__ == "__main__":
    # Example usage
    llm = get_llm_by_type("basic")
    print(f"Loaded LLM: {llm}")