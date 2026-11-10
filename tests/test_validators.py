"""Tests for utils/validators.py (no database needed)."""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from utils import validators as v
from utils.helpers import format_inr


def test_valid_amount_is_rounded_decimal():
    assert v.validate_amount("1,250.456") == Decimal("1250.46")
    assert v.validate_amount(500) == Decimal("500.00")


@pytest.mark.parametrize("bad", [0, -5, "abc", "", None, "nan", "inf", 10**12])
def test_invalid_amounts_rejected(bad):
    with pytest.raises(v.ValidationError):
        v.validate_amount(bad)


def test_transaction_type():
    assert v.validate_transaction_type(" deposit ") == "DEPOSIT"
    with pytest.raises(v.ValidationError):
        v.validate_transaction_type("TRANSFER")


def test_date_validation():
    assert v.validate_date("2026-03-25").day == 25
    assert v.validate_date("2026-03-25 10:30").hour == 10
    with pytest.raises(v.ValidationError):
        v.validate_date("25/03/2026")
    with pytest.raises(v.ValidationError):
        v.validate_date(date.today() + timedelta(days=5))
    assert v.validate_date(date.today() + timedelta(days=5), allow_future=True)


def test_phone_and_email():
    assert v.validate_phone("+91 98765-43210") == "9876543210"
    assert v.validate_email(" Test@Example.com ") == "test@example.com"
    with pytest.raises(v.ValidationError):
        v.validate_phone("12345")
    with pytest.raises(v.ValidationError):
        v.validate_email("not-an-email")


def test_name_account_number_and_id():
    assert v.validate_name("  Asha Rao ") == "Asha Rao"
    with pytest.raises(v.ValidationError):
        v.validate_name("R2D2")
    assert v.validate_account_number("1234567890") == "1234567890"
    with pytest.raises(v.ValidationError):
        v.validate_account_number("12AB")
    assert v.validate_id("7") == 7
    for bad in (0, -1, "x", None, True):
        with pytest.raises(v.ValidationError):
            v.validate_id(bad)


def test_account_type_and_status():
    assert v.validate_account_type("savings") == "SAVINGS"
    assert v.validate_account_status("inactive") == "INACTIVE"
    with pytest.raises(v.ValidationError):
        v.validate_account_type("GOLD")


def test_indian_currency_format():
    assert format_inr(1234567.5) == "₹12,34,567.50"
    assert format_inr(950) == "₹950.00"
    assert format_inr(-1500) == "-₹1,500.00"
