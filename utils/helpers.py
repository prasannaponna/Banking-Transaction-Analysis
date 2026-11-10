"""Small helper functions and constants used in many places."""
import uuid
from datetime import datetime
from decimal import Decimal

# Categories offered in dropdown lists (users can still type other categories in the backend)
EXPENSE_CATEGORIES = ["Food", "Shopping", "Transport", "Bills", "Education",
                      "Entertainment", "Health", "Travel", "Rent", "Other"]
INCOME_CATEGORIES = ["Salary", "Freelance", "Investment", "Gift", "Refund", "Other"]
ALL_CATEGORIES = sorted(set(EXPENSE_CATEGORIES + INCOME_CATEGORIES))

# Category used when an account is opened with money in it
OPENING_BALANCE_CATEGORY = "Opening Balance"


def format_inr(amount):
    """Format a number the Indian way: 1234567.5 -> '₹12,34,567.50'."""
    if amount is None:
        return "₹0.00"
    value = Decimal(str(amount)).quantize(Decimal("0.01"))
    sign = "-" if value < 0 else ""
    whole, fraction = f"{abs(value):.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups + [tail])
    return f"{sign}₹{whole}.{fraction}"


def generate_reference_number():
    """Unique reference such as TXN20260325A1B2C3D4."""
    return "TXN" + datetime.now().strftime("%Y%m%d") + uuid.uuid4().hex[:8].upper()


def generate_account_number():
    """Random 12-digit account number (the DB UNIQUE key rejects the rare duplicate)."""
    return "5" + str(uuid.uuid4().int)[:11]
