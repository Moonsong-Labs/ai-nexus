"""Common packages."""

import json
import uuid
from dataclasses import asdict
from datetime import datetime

from langchain_core.messages import (
    BaseMessage,
)
from langsmith import RunTree
from langsmith.client import Client
from langsmith.evaluation import EvaluationResult
from pydantic import BaseModel


class BaseMessageEncoder(json.JSONEncoder):
    """JSON encoder for BaseMessage."""

    def default(self, obj):  # noqa: D102
        if isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, "__dataclass_fields__"):  # Check if obj is a dataclass
            return asdict(obj)
        elif isinstance(obj, RunTree):
            return obj.dict()
        elif isinstance(obj, BaseMessage):
            return obj.model_dump()
        elif isinstance(obj, BaseModel):
            return obj.model_dump()
        elif isinstance(obj, EvaluationResult):
            return obj.dict()
        elif isinstance(obj, Client):  # Handle LangSmith Client
            return {
                "api_url": obj.api_url,
                "tenant_id": str(obj._tenant_id)
                if hasattr(obj, "_tenant_id")
                else None,
            }
        return super().default(obj)
