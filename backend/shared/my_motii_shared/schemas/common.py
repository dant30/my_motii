"""Common API schema primitives."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
	model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class AuditMetadata(APIModel):
	id: UUID
	created_at: datetime
	updated_at: datetime


class ErrorBody(APIModel):
	code: str
	message: str
	context: dict[str, Any] = Field(default_factory=dict)