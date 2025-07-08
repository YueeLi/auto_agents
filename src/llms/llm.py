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
    model_key = f"{llm_type.upper()}_MODEL"
    llm_config = conf.get(model_key)
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


if __name__ == "__main__":
    # Example usage
    # To run this example, ensure you have a conf.yaml with at least one model defined, e.g., BASIC_MODEL
    try:
        llm = get_llm_by_type("basic")
        print(f"Loaded LLM: {llm}")
        response = llm.invoke("你好")
        print(response)
    except ValueError as e:
        print(f"Error loading LLM: {e}")
        print("Please ensure your conf.yaml is configured correctly.")
