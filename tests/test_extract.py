"""Tests for the DocumentData checks in app/extract.py and the setup checks in app/llm.py."""

import pytest

from app.extract import DocumentData
from app.llm import ConfigError, get_model


def test_currency_is_upper_case(water_bill):
    assert water_bill.amounts[0].currency == "USD"


def test_good_dates_are_kept(water_bill):
    assert water_bill.issue_date == "2026-11-05"
    assert water_bill.deadlines[0].date == "2026-12-01"
    assert water_bill.unreadable_fields == []


def test_bad_dates_are_removed_and_marked_unreadable(water_bill):
    raw = water_bill.model_dump()
    raw["issue_date"] = "05/11/2026"  # not YYYY-MM-DD
    raw["deadlines"][0]["date"] = "2026-02-30"  # no such day
    data = DocumentData(**raw)
    assert data.issue_date is None
    assert data.deadlines[0].date is None
    assert data.unreadable_fields == ["issue_date", "deadlines[0].date"]


def test_missing_api_key_gives_a_clear_message(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "google_genai")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    with pytest.raises(ConfigError, match="GOOGLE_API_KEY"):
        get_model()


def test_unknown_provider_gives_a_clear_message(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nope")
    with pytest.raises(ConfigError, match="LLM_PROVIDER"):
        get_model()
