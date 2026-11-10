"""Transaction logic tests: deposit, withdrawal, balance rules (needs MySQL)."""
from datetime import date, timedelta
from decimal import Decimal

import pytest

from backend import account_service, balance_service, transaction_service
from backend.transaction_service import InsufficientBalanceError
from utils.validators import ValidationError

pytestmark = pytest.mark.usefixtures("require_database")


def test_opening_balance_is_a_deposit(account_id):
    assert balance_service.get_account_balance(account_id) == Decimal("1000.00")
    assert balance_service.calculate_balance(account_id) == Decimal("1000.00")


def test_deposit_increases_balance(account_id):
    transaction_service.deposit(account_id, 500, "Salary", "test deposit")
    assert balance_service.get_account_balance(account_id) == Decimal("1500.00")


def test_withdrawal_decreases_balance(account_id):
    transaction_service.withdraw(account_id, 300, "Food", "test withdrawal")
    assert balance_service.get_account_balance(account_id) == Decimal("700.00")


def test_insufficient_balance_rejected(account_id):
    with pytest.raises(InsufficientBalanceError):
        transaction_service.withdraw(account_id, 5000, "Shopping")
    assert balance_service.get_account_balance(account_id) == Decimal("1000.00")  # unchanged


@pytest.mark.parametrize("amount", [-100, 0, "abc"])
def test_invalid_amount_rejected(account_id, amount):
    with pytest.raises(ValidationError):
        transaction_service.add_transaction(account_id, "DEPOSIT", amount)


def test_invalid_type_account_and_date_rejected(account_id):
    with pytest.raises(ValidationError):
        transaction_service.add_transaction(account_id, "TRANSFER", 100)
    with pytest.raises(ValidationError):
        transaction_service.add_transaction(999999999, "DEPOSIT", 100)
    with pytest.raises(ValidationError):
        transaction_service.add_transaction(account_id, "DEPOSIT", 100, "not-a-date")
    with pytest.raises(ValidationError):
        transaction_service.add_transaction(account_id, "DEPOSIT", 100, date.today() + timedelta(days=3))


def test_inactive_account_rejected(account_id):
    account_service.deactivate_account(account_id)
    with pytest.raises(ValidationError):
        transaction_service.deposit(account_id, 100)


def test_balance_calculation_matches_stored_balance(account_id):
    transaction_service.deposit(account_id, 250)
    transaction_service.withdraw(account_id, 100)
    transaction_service.withdraw(account_id, 50)
    expected = Decimal("1100.00")
    assert balance_service.calculate_balance(account_id) == expected
    assert balance_service.get_account_balance(account_id) == expected


def test_update_and_delete_recalculate_balance(account_id):
    tx_id = transaction_service.withdraw(account_id, 200, "Food")
    transaction_service.update_transaction(tx_id, amount=300)
    assert balance_service.get_account_balance(account_id) == Decimal("700.00")
    transaction_service.delete_transaction(tx_id)
    assert balance_service.get_account_balance(account_id) == Decimal("1000.00")


def test_update_that_makes_balance_negative_is_rejected(account_id):
    tx_id = transaction_service.withdraw(account_id, 200, "Food")
    with pytest.raises(ValidationError):
        transaction_service.update_transaction(tx_id, amount=5000)
    assert balance_service.get_account_balance(account_id) == Decimal("800.00")


def test_filter_and_search(account_id):
    transaction_service.withdraw(account_id, 120, "Food", "unique-pizza-order")
    found = transaction_service.search_transactions("unique-pizza-order")
    assert len(found) == 1 and found[0]["category"] == "Food"
    only_food = transaction_service.get_transactions(account_id=account_id, category="Food",
                                                     transaction_type="WITHDRAWAL", min_amount=100)
    assert len(only_food) == 1
    assert transaction_service.get_transactions(account_id=account_id, min_amount=100000) == []


def test_sql_injection_text_is_harmless(account_id):
    assert transaction_service.search_transactions("'; DROP TABLE transactions; --") == []
    assert transaction_service.get_transactions(account_id=account_id)  # table still exists
