"""Tests for tenant execution context and query isolation."""

from uuid import uuid4

import pytest

from my_motii_shared.tenancy import (
    for_current_tenant,
    get_current_tenant,
    reset_current_tenant,
    set_current_tenant,
)


def test_tenant_context_can_be_set_and_reset():
    tenant_id = uuid4()
    token = set_current_tenant(tenant_id)
    try:
        assert get_current_tenant() == tenant_id
    finally:
        reset_current_tenant(token)
    assert get_current_tenant(required=False) is None


def test_missing_tenant_is_explicit_error():
    with pytest.raises(RuntimeError):
        get_current_tenant()


def test_query_is_filtered_by_current_tenant():
    tenant_id = uuid4()
    queryset = type("Query", (), {"filter": lambda self, **kwargs: kwargs})()
    token = set_current_tenant(tenant_id)
    try:
        assert for_current_tenant(queryset) == {"tenant_id": tenant_id}
    finally:
        reset_current_tenant(token)