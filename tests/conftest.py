"""Shared pytest setup. Database tests are skipped automatically when MySQL is not reachable."""
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # make backend/analysis/utils importable


def unique_phone():
    return "9" + str(uuid.uuid4().int)[:9]


def unique_email():
    return f"test_{uuid.uuid4().hex[:10]}@example.com"


@pytest.fixture(scope="session")
def require_database():
    from backend.db_connection import check_connection
    if not check_connection():
        pytest.skip("MySQL is not reachable. Check .env and run database/schema.sql first.")


@pytest.fixture
def customer_id(require_database):
    """A temporary customer that is removed (with its accounts/transactions) after the test."""
    from backend import customer_service
    from backend.db_connection import execute
    new_id = customer_service.create_customer("Test Customer", unique_phone(), unique_email(), "Test Address")
    yield new_id
    execute("DELETE FROM deleted_accounts WHERE customer_id = %s", (new_id,))
    execute("DELETE FROM transactions WHERE account_id IN (SELECT account_id FROM accounts WHERE customer_id = %s)",
            (new_id,))
    execute("DELETE FROM accounts WHERE customer_id = %s", (new_id,))
    execute("DELETE FROM customers WHERE customer_id = %s", (new_id,))


@pytest.fixture
def account_id(customer_id):
    """A SAVINGS account with an opening balance of 1000."""
    from backend import account_service
    return account_service.create_account(customer_id, "SAVINGS", opening_balance=1000)
