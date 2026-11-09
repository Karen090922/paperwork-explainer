"""Tests for find_unsupported_numbers() in app/explain.py.

Any number in an explanation that isn't in the document is a bug. These tests make
sure the check catches invented numbers without flagging correct ones.
"""

from app.explain import Explanation, find_unsupported_numbers


def make(text: str) -> Explanation:
    return Explanation(what_is_this=text, what_to_do=[], deadlines=[], if_ignored="")


def test_correct_numbers_pass(water_bill):
    text = "Pay 45.20 USD by December 1, 2026. Otherwise a 5.00 USD late fee is added, and after 30 days water may be cut off."
    assert find_unsupported_numbers(make(text), water_bill) == []


def test_other_number_formats_pass(water_bill):
    text = "Оплатите 45,20 USD до 01.12.2026. Счёт от 5 ноября 2026 г."
    assert find_unsupported_numbers(make(text), water_bill) == []


def test_invented_numbers_are_caught(water_bill):
    text = "Pay 54.20 USD within 14 days."
    assert find_unsupported_numbers(make(text), water_bill) == ["54.20", "14"]
