"""Shared test helpers. These tests run offline: no API key, no cost."""

import pytest

from app.extract import DocumentData


@pytest.fixture
def water_bill() -> DocumentData:
    """What a correct extraction of evals/test_docs/sample_water_bill.jpg looks like."""
    return DocumentData(
        is_readable=True,
        retake_tip=None,
        document_type="water bill",
        sender="Riverside Water Co.",
        issue_date="2026-11-05",
        amounts=[{"label": "Total due", "value": 45.20, "currency": "usd"}],
        deadlines=[{"what": "Pay the total due", "date": "2026-12-01"}],
        actions_required=["Pay 45.20 USD to Riverside Water Co."],
        consequences_if_ignored=[
            "A late fee of 5.00 USD is added to the next bill.",
            "Water service may be suspended 30 days after the due date.",
        ],
        language="English",
        unreadable_fields=[],
    )
