"""Utilities for the code agent."""

from typing import Tuple


def split_model_and_provider(model: str) -> Tuple[str, str]:
    """Split a model string into provider and model name."""
    provider, model_name = model.split("/", 1)
    return provider, model_name 