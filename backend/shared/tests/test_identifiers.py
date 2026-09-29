"""Tests for UUID identifier helpers."""

from uuid import UUID

import pytest

from my_motii_shared.domain.identifiers import new_id, parse_id


def test_new_id_returns_uuid_and_string_parse_round_trips():
    value = new_id()

    assert isinstance(value, UUID)
    assert parse_id(str(value)) == value


def test_parse_id_rejects_invalid_input():
    with pytest.raises(ValueError):
        parse_id("not-a-uuid")