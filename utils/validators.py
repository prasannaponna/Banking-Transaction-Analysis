"""
Input validators (shared by backend, tests and dashboard).

Every validate_* function either returns a clean value or raises
ValidationError with a friendly message. They never touch the database.
"""
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

VALID_TRANSACTION_TYPES = ("DEPOSIT", "WITHDRAWAL")
VALID_ACCOUNT_TYPES = ("SAVINGS", "CURRENT")
VALID_ACCOUNT_STATUSES = ("ACTIVE", "INACTIVE")
MAX_TRANSACTION_AMOUNT = Decimal("100000000")  # 10 crore, a sanity limit

_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,99}$")
_EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_PHONE_PATTERN = re.compile(r"^[6-9]\d{9}$")  # 10-digit Indian mobile number
_ACCOUNT_NUMBER_PATTERN = re.compile(r"^\d{10,16}$")
_DATE_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d")


class ValidationError(ValueError):
    """Raised when user input or a business rule is not acceptable."""


def validate_id(value, field_name="ID"):
    """Return a positive integer ID."""
    if isinstance(value, bool):
        raise ValidationError(f"{field_name} must be a positive whole number.")
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a positive whole number.")
    if number <= 0 or str(value).strip() != str(number):
        raise ValidationError(f"{field_name} must be a positive whole number.")
    return number


def validate_name(name):
    name = (name or "").strip()
    if not _NAME_PATTERN.match(name):
        raise ValidationError(
            "Name must be 2-100 characters and contain only letters, spaces, . ' -"
        )
    return name


def validate_phone(phone):
    """Accepts '9876543210', '+91 98765 43210', '98765-43210'. Returns 10 digits."""
    cleaned = re.sub(r"[\s-]", "", str(phone or ""))
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    if not _PHONE_PATTERN.match(cleaned):
        raise ValidationError("Phone must be a valid 10-digit mobile number (starting with 6-9).")
    return cleaned


def validate_email(email):
    email = (email or "").strip().lower()
    if len(email) > 120 or not _EMAIL_PATTERN.match(email):
        raise ValidationError("Please enter a valid email address.")
    return email


def validate_address(address):
    address = (address or "").strip()
    if len(address) > 255:
        raise ValidationError("Address can be at most 255 characters.")
    return address or None


def validate_account_number(account_number):
    account_number = str(account_number or "").strip()
    if not _ACCOUNT_NUMBER_PATTERN.match(account_number):
        raise ValidationError("Account number must contain 10 to 16 digits.")
    return account_number


def validate_account_type(account_type):
    account_type = str(account_type or "").strip().upper()
    if account_type not in VALID_ACCOUNT_TYPES:
        raise ValidationError(f"Account type must be one of: {', '.join(VALID_ACCOUNT_TYPES)}.")
    return account_type


def validate_account_status(status):
    status = str(status or "").strip().upper()
    if status not in VALID_ACCOUNT_STATUSES:
        raise ValidationError(f"Status must be one of: {', '.join(VALID_ACCOUNT_STATUSES)}.")
    return status


def validate_transaction_type(transaction_type):
    transaction_type = str(transaction_type or "").strip().upper()
    if transaction_type not in VALID_TRANSACTION_TYPES:
        raise ValidationError(
            f"Transaction type must be one of: {', '.join(VALID_TRANSACTION_TYPES)}."
        )
    return transaction_type


def validate_amount(amount, allow_zero=False):
    """Return the amount as a Decimal rounded to 2 places."""
    if isinstance(amount, bool) or amount is None or str(amount).strip() == "":
        raise ValidationError("Amount is required.")
    try:
        value = Decimal(str(amount).replace(",", "").strip())
    except InvalidOperation:
        raise ValidationError("Amount must be a number.")
    if not value.is_finite():
        raise ValidationError("Amount must be a number.")
    value = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if value < 0 or (value == 0 and not allow_zero):
        raise ValidationError("Amount must be greater than zero.")
    if value > MAX_TRANSACTION_AMOUNT:
        raise ValidationError(f"Amount cannot exceed {MAX_TRANSACTION_AMOUNT:,}.")
    return value


def validate_date(value, allow_future=False):
    """Return a datetime. Accepts datetime, date or 'YYYY-MM-DD[ HH:MM[:SS]]' text."""
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, date):
        result = datetime(value.year, value.month, value.day)
    else:
        text = str(value or "").strip()
        result = None
        for date_format in _DATE_FORMATS:
            try:
                result = datetime.strptime(text, date_format)
                break
            except ValueError:
                continue
        if result is None:
            raise ValidationError("Date must look like YYYY-MM-DD (for example 2026-03-25).")
    if result.year < 1990:
        raise ValidationError("Date is too old to be valid.")
    if not allow_future and result.date() > date.today():
        raise ValidationError("Transaction date cannot be in the future.")
    return result


def validate_category(category):
    category = (category or "").strip()
    if not category:
        raise ValidationError("Category is required.")
    if len(category) > 50:
        raise ValidationError("Category can be at most 50 characters.")
    return category.title() if category.islower() else category


def validate_description(description):
    description = (description or "").strip()
    if len(description) > 255:
        raise ValidationError("Description can be at most 255 characters.")
    return description or None
