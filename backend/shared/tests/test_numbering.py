"""Tests for document-number formatting."""

import pytest

from my_motii_shared.domain.numbering import DocumentNumber, format_document_number


def test_document_number_formats_sequence_with_fixed_width():
    assert format_document_number("KIR01", "INV", 2026, 12) == "KIR01-INV-2026-00012"


def test_document_number_rejects_invalid_sequence():
    with pytest.raises(ValueError):
        DocumentNumber("KIR01", "INV", 2026, 0)