"""Validated pagination request and response schemas."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageRequest(BaseModel):
	page: int = Field(default=1, ge=1)
	page_size: int = Field(default=50, ge=1, le=200)

	@property
	def offset(self) -> int:
		return (self.page - 1) * self.page_size


class Page(BaseModel, Generic[T]):
	items: list[T]
	total: int = Field(ge=0)
	page: int = Field(ge=1)
	page_size: int = Field(ge=1)