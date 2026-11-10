"""Account CRUD (MEMBER 1)."""
import json
from datetime import datetime

from backend.db_connection import DuplicateEntryError, execute, fetch_all, fetch_one, get_cursor
from backend.transaction_service import apply_transaction
from utils.helpers import OPENING_BALANCE_CATEGORY, generate_account_number, generate_reference_number
from utils.validators import (ValidationError, validate_account_number, validate_account_status,
                              validate_account_type, validate_amount, validate_id)

_SELECT_ACCOUNTS = """
    SELECT a.account_id, a.customer_id, c.name AS customer_name, a.account_number,
           a.account_type, a.balance, a.status, a.created_at
    FROM accounts a
    JOIN customers c ON c.customer_id = a.customer_id
"""


def create_account(customer_id, account_type, opening_balance=0, account_number=None):
    """
    Open a new account for an existing customer and return the new account_id.
    A non-zero opening balance is stored as a DEPOSIT transaction, so the balance
    always equals the sum of the transactions.
    """
    customer_id = validate_id(customer_id, "Customer ID")
    account_type = validate_account_type(account_type)
    opening_balance = validate_amount(opening_balance or 0, allow_zero=True)
    account_number = validate_account_number(account_number) if account_number else generate_account_number()

    try:
        with get_cursor(commit=True) as cursor:
            cursor.execute("SELECT customer_id FROM customers WHERE customer_id = %s", (customer_id,))
            if cursor.fetchone() is None:
                raise ValidationError("Customer not found. Create the customer first.")
            cursor.execute(
                "INSERT INTO accounts (customer_id, account_number, account_type, balance, status) "
                "VALUES (%s, %s, %s, 0, 'ACTIVE')",
                (customer_id, account_number, account_type),
            )
            account_id = cursor.lastrowid
            if opening_balance > 0:
                apply_transaction(cursor, account_id, "DEPOSIT", opening_balance, datetime.now(),
                                  OPENING_BALANCE_CATEGORY, "Opening balance", generate_reference_number())
            return account_id
    except DuplicateEntryError:
        raise ValidationError("An account with this account number already exists.")


def get_account(account_id):
    account_id = validate_id(account_id, "Account ID")
    return fetch_one(_SELECT_ACCOUNTS + " WHERE a.account_id = %s", (account_id,))


def get_all_accounts(status=None):
    """All accounts, or only 'ACTIVE' / 'INACTIVE' ones."""
    if status:
        return fetch_all(_SELECT_ACCOUNTS + " WHERE a.status = %s ORDER BY a.account_id",
                         (validate_account_status(status),))
    return fetch_all(_SELECT_ACCOUNTS + " ORDER BY a.account_id")


def get_accounts_by_customer(customer_id):
    customer_id = validate_id(customer_id, "Customer ID")
    return fetch_all(_SELECT_ACCOUNTS + " WHERE a.customer_id = %s ORDER BY a.account_id", (customer_id,))


def count_accounts():
    return fetch_one("SELECT COUNT(*) AS total FROM accounts")["total"]


def search_accounts(keyword):
    """Search by account number, customer name, account type or status."""
    pattern = f"%{(keyword or '').strip()}%"
    return fetch_all(
        _SELECT_ACCOUNTS + " WHERE a.account_number LIKE %s OR c.name LIKE %s "
        "OR a.account_type LIKE %s OR a.status LIKE %s ORDER BY a.account_id",
        (pattern, pattern, pattern, pattern),
    )


def update_account(account_id, account_type=None, status=None):
    """Change the account type and/or status. The balance can only change via transactions."""
    account_id = validate_id(account_id, "Account ID")
    if get_account(account_id) is None:
        raise ValidationError("Account not found.")
    updates, params = [], []
    if account_type is not None:
        updates.append("account_type = %s")
        params.append(validate_account_type(account_type))
    if status is not None:
        updates.append("status = %s")
        params.append(validate_account_status(status))
    if not updates:
        raise ValidationError("Nothing to update.")
    params.append(account_id)
    _, changed = execute(f"UPDATE accounts SET {', '.join(updates)} WHERE account_id = %s", tuple(params))
    return changed > 0


def deactivate_account(account_id):
    """Accounts are deactivated, not deleted, so the transaction history is kept."""
    return update_account(account_id, status="INACTIVE")


def activate_account(account_id):
    return update_account(account_id, status="ACTIVE")


def count_transactions(account_id):
    """Number of transactions recorded for an account (0 is safe to delete directly)."""
    account_id = validate_id(account_id, "Account ID")
    return fetch_one("SELECT COUNT(*) AS total FROM transactions WHERE account_id = %s",
                     (account_id,))["total"]


def delete_account(account_id, delete_transactions=False):
    """
    Move an account to the recycle bin and delete it (it can be restored later).

    Before the rows are removed, a copy of the account and a JSON snapshot of its
    transactions is stored in deleted_accounts, so nothing is lost. The transactions
    table references accounts with ON DELETE RESTRICT, so an account that already has
    history can only be removed when the caller explicitly opts in with
    delete_transactions=True. Everything happens in one DB transaction.
    """
    account_id = validate_id(account_id, "Account ID")
    account = get_account(account_id)
    if account is None:
        raise ValidationError("Account not found.")

    total = count_transactions(account_id)
    if total > 0 and not delete_transactions:
        raise ValidationError(
            f"This account has {total} transaction(s). Confirm the deletion of its "
            "transactions, or deactivate the account instead to keep the history."
        )

    with get_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO deleted_accounts (account_id, customer_id, customer_name, account_number, "
            "account_type, balance, status, account_created_at, transaction_count, transactions_json) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (account["account_id"], account["customer_id"], account["customer_name"],
             account["account_number"], account["account_type"], account["balance"],
             account["status"], account["created_at"], total,
             _transactions_snapshot(cursor, account_id)),
        )
        if total > 0:
            cursor.execute("DELETE FROM transactions WHERE account_id = %s", (account_id,))
        cursor.execute("DELETE FROM accounts WHERE account_id = %s", (account_id,))
        return cursor.rowcount > 0


def _transactions_snapshot(cursor, account_id):
    """JSON copy of an account's transactions, stored in the recycle bin for restore."""
    cursor.execute(
        "SELECT transaction_date, transaction_type, amount, category, description, "
        "reference_number, created_at FROM transactions WHERE account_id = %s "
        "ORDER BY transaction_date, transaction_id",
        (account_id,),
    )
    return json.dumps(cursor.fetchall(), default=str)


def get_deleted_accounts(limit=25):
    """Recently deleted accounts (newest first) for the 'Recently Deleted' tab."""
    return fetch_all(
        "SELECT id, account_id, customer_id, customer_name, account_number, account_type, "
        "balance, status, transaction_count, deleted_at, restored_at "
        "FROM deleted_accounts ORDER BY deleted_at DESC, id DESC LIMIT %s",
        (int(limit),),
    )


def restore_account(archive_id):
    """
    Put a deleted account back, together with its transactions.

    The original account_id is reused when it is still free. Restoring is refused if
    the account number is taken again or the customer no longer exists, so the data
    stays consistent. Returns the (possibly new) account_id.
    """
    archive_id = validate_id(archive_id, "Deleted account ID")
    row = fetch_one("SELECT * FROM deleted_accounts WHERE id = %s", (archive_id,))
    if row is None:
        raise ValidationError("Deleted account not found.")
    if row["restored_at"] is not None:
        raise ValidationError("This account has already been restored.")
    if fetch_one("SELECT account_id FROM accounts WHERE account_number = %s",
                 (row["account_number"],)):
        raise ValidationError(
            "An account with this account number already exists, so it cannot be restored."
        )

    transactions = json.loads(row["transactions_json"] or "[]")

    try:
        with get_cursor(commit=True) as cursor:
            cursor.execute("SELECT customer_id FROM customers WHERE customer_id = %s",
                           (row["customer_id"],))
            if cursor.fetchone() is None:
                raise ValidationError("The customer no longer exists, so the account cannot be restored.")

            cursor.execute("SELECT account_id FROM accounts WHERE account_id = %s",
                           (row["account_id"],))
            if cursor.fetchone() is None:  # keep the original ID so history stays linked
                cursor.execute(
                    "INSERT INTO accounts (account_id, customer_id, account_number, account_type, "
                    "balance, created_at, status) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (row["account_id"], row["customer_id"], row["account_number"],
                     row["account_type"], row["balance"], row["account_created_at"], row["status"]),
                )
                account_id = row["account_id"]
            else:
                cursor.execute(
                    "INSERT INTO accounts (customer_id, account_number, account_type, balance, "
                    "created_at, status) VALUES (%s, %s, %s, %s, %s, %s)",
                    (row["customer_id"], row["account_number"], row["account_type"],
                     row["balance"], row["account_created_at"], row["status"]),
                )
                account_id = cursor.lastrowid

            for transaction in transactions:
                cursor.execute(
                    "INSERT INTO transactions (account_id, transaction_date, transaction_type, amount, "
                    "category, description, reference_number, created_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (account_id, transaction["transaction_date"], transaction["transaction_type"],
                     transaction["amount"], transaction["category"], transaction["description"],
                     transaction["reference_number"], transaction["created_at"]),
                )

            cursor.execute("UPDATE deleted_accounts SET restored_at = NOW() WHERE id = %s",
                           (archive_id,))
            return account_id
    except DuplicateEntryError:
        raise ValidationError(
            "A transaction reference from this account is already in use, so it cannot be restored."
        )


def purge_deleted_account(archive_id):
    """Remove one entry from the recycle bin permanently (the account cannot come back)."""
    archive_id = validate_id(archive_id, "Deleted account ID")
    if fetch_one("SELECT id FROM deleted_accounts WHERE id = %s", (archive_id,)) is None:
        raise ValidationError("Deleted account not found.")
    _, deleted = execute("DELETE FROM deleted_accounts WHERE id = %s", (archive_id,))
    return deleted > 0
