"""Utility functions used in our graph."""


def split_model_and_provider(fully_specified_name: str) -> dict:
    """
    Splits a fully specified model name into provider and model components.
    
    If the input string contains a "/", the part before the first slash is treated as the provider and the part after as the model. If no slash is present, the provider is set to None and the entire string is used as the model.
    
    Args:
        fully_specified_name: The string representing the fully specified model name, optionally including a provider prefix separated by "/".
    
    Returns:
        A dictionary with keys "model" and "provider" containing the extracted model name and provider, respectively.
    """
    if "/" in fully_specified_name:
        provider, model = fully_specified_name.split("/", maxsplit=1)
    else:
        provider = None
        model = fully_specified_name
    return {"model": model, "provider": provider}
