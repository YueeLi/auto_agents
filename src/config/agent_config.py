# Copyright (c) 2025 Bytedance Ltd. and/or its affiliates
# SPDX-License-Identifier: MIT

from typing import Literal
from src.config.yaml_loader import load_yaml_config
from pathlib import Path


# Dynamically load LLM types from conf.yaml
def get_llm_types():
    conf_path = Path(__file__).parent.parent.parent / "conf.yaml"
    config = load_yaml_config(str(conf_path.resolve()))
    # Extract model types from keys like "BASIC_MODEL", "REASONING_MODEL", etc.
    return [key.replace('_MODEL', '').lower() for key in config.keys() if key.endswith('_MODEL')]


LLM_TYPES = get_llm_types()
LLMType = Literal[tuple(LLM_TYPES)]

# Define agent-LLM mapping
# Ensure that the default LLM type ('basic') is available
DEFAULT_LLM_TYPE = "basic" if "basic" in LLM_TYPES else (LLM_TYPES[0] if LLM_TYPES else None)
