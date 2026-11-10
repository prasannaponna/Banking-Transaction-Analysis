"""Database tests: connection, tables and customer/account CRUD (needs MySQL)."""
import pytest

from backend import account_service, customer_service
from backend.db_connection import check_connection, fetch_all
from tests.conftest import unique_email, unique_phone
from utils.validators import ValidationError

pytestmark = pytest.mark.usefixtures("require_database")


def test_database_connection():
    assert check_connection() is True


def test_tables_exist():
    tables = {list(row.values())[0] for row in fetch_all("SHOW TABLES")}
    assert {"customers", "accounts", "transactions", "deleted_accounts"} <= tables


def test_customer_create_read_update_search_delete():
    new_id = customer_service.create_customer("Crud Tester", unique_phone(), unique_email(), "Somewhere")
    try:
        assert customer_service.get_customer(new_id)["name"] == "Crud Tester"
        assert customer_service.update_customer(new_id, name="Crud Updated") is True
        assert customer_service.get_customer(new_id)["name"] == "Crud Updated"
        assert any(c["customer_id"] == new_id for c in customer_service.search_customers("Crud Updated"))
    finally:
        customer_service.delete_customer(new_id)
    assert customer_service.get_customer(new_id) is None


def test_duplicate_customer_rejected(customer_id):
    existing = customer_service.get_customer(customer_id)
    with pytest.raises(ValidationError):
        customer_service.create_customer("Another Person", existing["phone"], unique_email())


def test_invalid_customer_input_rejected(require_database):
    with pytest.raises(ValidationError):
        customer_service.create_customer("A", "123", "bad-email")


def test_account_creation_and_duplicate_number(customer_id):
    account_id = account_service.create_account(customer_id, "CURRENT", 0, "9999000011112222")
    assert account_service.get_account(account_id)["account_number"] == "9999000011112222"
    with pytest.raises(ValidationError):
        account_service.create_account(customer_id, "SAVINGS", 0, "9999000011112222")


def test_account_for_missing_customer_rejected(require_database):
    with pytest.raises(ValidationError):
        account_service.create_account(999999999, "SAVINGS")


def test_deactivate_account_and_customer_delete_blocked(account_id, customer_id):
    assert account_service.deactivate_account(account_id) is True
    assert account_service.get_account(account_id)["status"] == "INACTIVE"
    with pytest.raises(ValidationError):  # customer still owns an account
        customer_service.delete_customer(customer_id)


def test_delete_account_requires_history_confirmation(account_id):
    """An account with transactions is only deleted when history deletion is confirmed."""
    assert account_service.count_transactions(account_id) == 1  # opening balance

    with pytest.raises(ValidationError):
        account_service.delete_account(account_id)
    assert account_service.get_account(account_id) is not None  # still there

    assert account_service.delete_account(account_id, delete_transactions=True) is True
    assert account_service.get_account(account_id) is None
    assert account_service.count_transactions(account_id) == 0


def test_deleted_account_is_archived_and_can_be_restored(account_id):
    """Deleting moves the account to the recycle bin; restoring brings back its history."""
    account = account_service.get_account(account_id)

    assert account_service.delete_account(account_id, delete_transactions=True) is True
    assert account_service.get_account(account_id) is None

    archived = [row for row in account_service.get_deleted_accounts()
                if row["account_number"] == account["account_number"]]
    assert archived, "the deleted account should be stored in the recycle bin"
    entry = archived[0]
    assert entry["restored_at"] is None
    assert entry["transaction_count"] == 1
    assert entry["customer_name"] == account["customer_name"]

    restored_id = account_service.restore_account(entry["id"])
    restored = account_service.get_account(restored_id)
    assert restored["account_number"] == account["account_number"]
    assert restored["balance"] == account["balance"]
    assert account_service.count_transactions(restored_id) == 1

    with pytest.raises(ValidationError):  # cannot restore the same entry twice
        account_service.restore_account(entry["id"])


def test_purge_deleted_account_removes_it_permanently(account_id):
    account = account_service.get_account(account_id)
    assert account_service.delete_account(account_id, delete_transactions=True) is True

    entry = next(row for row in account_service.get_deleted_accounts()
                 if row["account_number"] == account["account_number"])
    assert account_service.purge_deleted_account(entry["id"]) is True
    assert all(row["id"] != entry["id"] for row in account_service.get_deleted_accounts())

    with pytest.raises(ValidationError):  # nothing left to purge
        account_service.purge_deleted_account(entry["id"])

