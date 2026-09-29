"""Tests for shared API schemas."""

import pytest
from pydantic import ValidationError

from my_motii_shared.schemas import ErrorBody, PageRequest


def test_page_request_computes_offset():
    request = PageRequest(page=3, page_size=20)

    assert request.offset == 40


def test_page_request_rejects_out_of_range_values():
    with pytest.raises(ValidationError):
        PageRequest(page=0)
    with pytest.raises(ValidationError):
        PageRequest(page_size=201)


def test_error_body_context_defaults_per_instance():
    first = ErrorBody(code="bad", message="Invalid")
    second = ErrorBody(code="bad", message="Invalid")

    first.context["field"] = "sku"
    assert second.context == {}