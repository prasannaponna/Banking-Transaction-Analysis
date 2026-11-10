"""Balance calculation (MEMBER 1)."""
from backend.db_connection import fetch_all, fetch_one
from utils.validators import ValidationError, validate_id

_BALANCE_SQL = """
    SELECT COALESCE(SUM(CASE WHEN transaction_type = 'DEPOSIT' THEN amount ELSE -amount END), 0) AS balance
    FROM transactions
    WHERE account_id = %s
"""


def calculate_balance(account_id):
    """Balance worked out from the transactions (deposits - withdrawals)."""
    account_id = validate_id(account_id, "Account ID")
    return fetch_one(_BALANCE_SQL, (account_id,))["balance"]


def get_account_balance(account_id):
    """Balance stored in the accounts table."""
    account_id = validate_id(account_id, "Account ID")
    row = fetch_one("SELECT balance FROM accounts WHERE account_id = %s", (account_id,))
    if row is None:
        raise ValidationError("Account not found.")
    return row["balance"]


def recalculate_balance_in_cursor(cursor, account_id):
    """
    Recalculate the balance from transactions and save it to the accounts table.
    Uses an existing cursor so the caller controls the commit/rollback.
    """
    cursor.execute(_BALANCE_SQL, (account_id,))
    new_balance = cursor.fetchone()["balance"]
    if new_balance < 0:
        raise ValidationError("This change would make the account balance negative.")
    cursor.execute("UPDATE accounts SET balance = %s WHERE account_id = %s", (new_balance, account_id))
    return new_balance


def get_total_balance():
    """Sum of the balances of all ACTIVE accounts."""
    row = fetch_one("SELECT COALESCE(SUM(balance), 0) AS total FROM accounts WHERE status = 'ACTIVE'")
    return row["total"]


def find_balance_mismatches():
    """List accounts whose stored balance differs from the transaction total (data check)."""
    return fetch_all(
        """
        SELECT a.account_id, a.account_number, a.balance AS stored_balance,
               COALESCE(SUM(CASE WHEN t.transaction_type = 'DEPOSIT' THEN t.amount ELSE -t.amount END), 0)
                   AS calculated_balance
        FROM accounts a
        LEFT JOIN transactions t ON t.account_id = a.account_id
        GROUP BY a.account_id, a.account_number, a.balance
        HAVING stored_balance <> calculated_balance
        """
    )
