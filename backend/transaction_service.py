"""Transaction operations: deposit, withdrawal, CRUD, search and filters (MEMBER 1)."""
from datetime import datetime, timedelta

from backend.balance_service import recalculate_balance_in_cursor
from backend.db_connection import DuplicateEntryError, fetch_all, fetch_one, get_cursor
from utils.helpers import generate_reference_number
from utils.validators import (ValidationError, validate_amount, validate_category, validate_date,
                              validate_description, validate_id, validate_transaction_type)


class InsufficientBalanceError(ValidationError):
    """Withdrawal is bigger than the money available in the account."""


# Columns returned to the dashboard / analysis (joined with account and customer)
_SELECT_TRANSACTIONS = """
    SELECT t.transaction_id, t.account_id, a.account_number, c.name AS customer_name,
           t.transaction_date, t.transaction_type, t.amount, t.category,
           t.description, t.reference_number, t.created_at
    FROM transactions t
    JOIN accounts  a ON a.account_id  = t.account_id
    JOIN customers c ON c.customer_id = a.customer_id
"""


def apply_transaction(cursor, account_id, transaction_type, amount, transaction_date,
                      category, description, reference_number):
    """
    Core deposit/withdrawal logic. Works on an open cursor so that callers
    (add_transaction, create_account) can include it in their own DB transaction.
    Expects already-validated values. Returns the new transaction_id.
    """
    # Lock the account row so two withdrawals cannot spend the same money
    cursor.execute("SELECT balance, status FROM accounts WHERE account_id = %s FOR UPDATE", (account_id,))
    account = cursor.fetchone()
    if account is None:
        raise ValidationError("Account not found. Please choose a valid account.")
    if account["status"] != "ACTIVE":
        raise ValidationError("This account is inactive. Activate it before adding transactions.")

    if transaction_type == "WITHDRAWAL":
        if account["balance"] < amount:
            raise InsufficientBalanceError("Insufficient balance for this withdrawal.")
        new_balance = account["balance"] - amount
    else:
        new_balance = account["balance"] + amount

    cursor.execute(
        """
        INSERT INTO transactions
            (account_id, transaction_date, transaction_type, amount, category, description, reference_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (account_id, transaction_date, transaction_type, amount, category, description, reference_number),
    )
    new_transaction_id = cursor.lastrowid
    cursor.execute("UPDATE accounts SET balance = %s WHERE account_id = %s", (new_balance, account_id))
    return new_transaction_id


def add_transaction(account_id, transaction_type, amount, transaction_date=None,
                    category="Other", description=None, reference_number=None):
    """Validate the input, then record a deposit or withdrawal. Returns transaction_id."""
    account_id = validate_id(account_id, "Account ID")
    transaction_type = validate_transaction_type(transaction_type)
    amount = validate_amount(amount)
    transaction_date = validate_date(transaction_date) if transaction_date else datetime.now()
    category = validate_category(category)
    description = validate_description(description)
    reference_number = (reference_number or "").strip() or generate_reference_number()
    if len(reference_number) > 30:
        raise ValidationError("Reference number can be at most 30 characters.")

    try:
        with get_cursor(commit=True) as cursor:
            return apply_transaction(cursor, account_id, transaction_type, amount,
                                     transaction_date, category, description, reference_number)
    except DuplicateEntryError:
        raise ValidationError("This reference number is already used by another transaction.")


def deposit(account_id, amount, category="Salary", description=None, transaction_date=None):
    return add_transaction(account_id, "DEPOSIT", amount, transaction_date, category, description)


def withdraw(account_id, amount, category="Other", description=None, transaction_date=None):
    return add_transaction(account_id, "WITHDRAWAL", amount, transaction_date, category, description)


def get_transaction(transaction_id):
    transaction_id = validate_id(transaction_id, "Transaction ID")
    return fetch_one(_SELECT_TRANSACTIONS + " WHERE t.transaction_id = %s", (transaction_id,))


def get_transactions(account_id=None, start_date=None, end_date=None, transaction_type=None,
                     category=None, min_amount=None, max_amount=None, keyword=None, limit=None):
    """
    View / filter / search transactions (newest first). All arguments are optional.
    The WHERE text is built only from fixed strings; user values go in `params`.
    """
    conditions, params = [], []

    if account_id:
        conditions.append("t.account_id = %s")
        params.append(validate_id(account_id, "Account ID"))
    if start_date:
        conditions.append("t.transaction_date >= %s")
        params.append(validate_date(start_date, allow_future=True).replace(hour=0, minute=0, second=0))
    if end_date:  # end date is inclusive, so compare with the start of the next day
        end = validate_date(end_date, allow_future=True)
        conditions.append("t.transaction_date < %s")
        params.append(datetime(end.year, end.month, end.day) + timedelta(days=1))
    if transaction_type:
        conditions.append("t.transaction_type = %s")
        params.append(validate_transaction_type(transaction_type))
    if category:
        conditions.append("t.category = %s")
        params.append(str(category).strip())
    if min_amount not in (None, ""):
        conditions.append("t.amount >= %s")
        params.append(validate_amount(min_amount, allow_zero=True))
    if max_amount not in (None, ""):
        conditions.append("t.amount <= %s")
        params.append(validate_amount(max_amount, allow_zero=True))
    if keyword and str(keyword).strip():
        pattern = f"%{str(keyword).strip()}%"
        conditions.append(
            "(t.description LIKE %s OR t.reference_number LIKE %s OR t.category LIKE %s OR a.account_number LIKE %s)"
        )
        params.extend([pattern] * 4)

    sql = _SELECT_TRANSACTIONS
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY t.transaction_date DESC, t.transaction_id DESC"
    if limit:
        sql += " LIMIT %s"
        params.append(int(validate_id(limit, "Limit")))
    return fetch_all(sql, tuple(params))


def search_transactions(keyword):
    """Search description, reference number, category or account number."""
    return get_transactions(keyword=keyword)


def update_transaction(transaction_id, transaction_type=None, amount=None, transaction_date=None,
                       category=None, description=None):
    """
    Edit a transaction (the account cannot be changed). The balance is recalculated
    afterwards; the change is rejected if the balance would become negative.
    """
    transaction_id = validate_id(transaction_id, "Transaction ID")
    updates, params = [], []
    if transaction_type is not None:
        updates.append("transaction_type = %s")
        params.append(validate_transaction_type(transaction_type))
    if amount is not None:
        updates.append("amount = %s")
        params.append(validate_amount(amount))
    if transaction_date is not None:
        updates.append("transaction_date = %s")
        params.append(validate_date(transaction_date))
    if category is not None:
        updates.append("category = %s")
        params.append(validate_category(category))
    if description is not None:
        updates.append("description = %s")
        params.append(validate_description(description))
    if not updates:
        raise ValidationError("Nothing to update.")

    with get_cursor(commit=True) as cursor:
        cursor.execute("SELECT account_id FROM transactions WHERE transaction_id = %s FOR UPDATE",
                       (transaction_id,))
        existing = cursor.fetchone()
        if existing is None:
            raise ValidationError("Transaction not found.")
        account_id = existing["account_id"]
        cursor.execute("SELECT account_id FROM accounts WHERE account_id = %s FOR UPDATE", (account_id,))

        cursor.execute(f"UPDATE transactions SET {', '.join(updates)} WHERE transaction_id = %s",
                       tuple(params + [transaction_id]))
        recalculate_balance_in_cursor(cursor, account_id)  # raises ValidationError if balance < 0
    return True


def delete_transaction(transaction_id):
    """Delete a transaction and fix the balance (rejected if the balance would go negative)."""
    transaction_id = validate_id(transaction_id, "Transaction ID")
    with get_cursor(commit=True) as cursor:
        cursor.execute("SELECT account_id FROM transactions WHERE transaction_id = %s FOR UPDATE",
                       (transaction_id,))
        existing = cursor.fetchone()
        if existing is None:
            raise ValidationError("Transaction not found.")
        account_id = existing["account_id"]
        cursor.execute("SELECT account_id FROM accounts WHERE account_id = %s FOR UPDATE", (account_id,))
        cursor.execute("DELETE FROM transactions WHERE transaction_id = %s", (transaction_id,))
        recalculate_balance_in_cursor(cursor, account_id)
    return True


def get_categories():
    """Distinct categories currently used in the transactions table."""
    return [row["category"] for row in fetch_all("SELECT DISTINCT category FROM transactions ORDER BY category")]


def get_date_range():
    """(earliest_date, latest_date) of all transactions, or None if there are none."""
    row = fetch_one("SELECT MIN(transaction_date) AS first_date, MAX(transaction_date) AS last_date FROM transactions")
    if not row or row["first_date"] is None:
        return None
    return row["first_date"].date(), row["last_date"].date()
