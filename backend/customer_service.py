"""Customer CRUD (MEMBER 1)."""
from backend.db_connection import DuplicateEntryError, execute, fetch_all, fetch_one
from utils.validators import (ValidationError, validate_address, validate_email, validate_id,
                              validate_name, validate_phone)


def create_customer(name, phone, email, address=None):
    """Add a customer and return the new customer_id."""
    values = (validate_name(name), validate_phone(phone), validate_email(email), validate_address(address))
    try:
        new_id, _ = execute(
            "INSERT INTO customers (name, phone, email, address) VALUES (%s, %s, %s, %s)", values
        )
    except DuplicateEntryError:
        raise ValidationError("A customer with this phone number or email already exists.")
    return new_id


def get_customer(customer_id):
    """Return one customer as a dict, or None if not found."""
    customer_id = validate_id(customer_id, "Customer ID")
    return fetch_one("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))


def get_all_customers():
    return fetch_all("SELECT * FROM customers ORDER BY customer_id")


def count_customers():
    return fetch_one("SELECT COUNT(*) AS total FROM customers")["total"]


def search_customers(keyword):
    """Search by name, phone, email or customer ID."""
    pattern = f"%{(keyword or '').strip()}%"
    return fetch_all(
        """
        SELECT * FROM customers
        WHERE name LIKE %s OR phone LIKE %s OR email LIKE %s OR CAST(customer_id AS CHAR) LIKE %s
        ORDER BY customer_id
        """,
        (pattern, pattern, pattern, pattern),
    )


def update_customer(customer_id, name=None, phone=None, email=None, address=None):
    """Update only the fields that are given (not None). Returns True if a row changed."""
    customer_id = validate_id(customer_id, "Customer ID")
    if get_customer(customer_id) is None:
        raise ValidationError("Customer not found.")

    # The column names below are fixed strings written by us, not user input.
    updates, params = [], []
    if name is not None:
        updates.append("name = %s")
        params.append(validate_name(name))
    if phone is not None:
        updates.append("phone = %s")
        params.append(validate_phone(phone))
    if email is not None:
        updates.append("email = %s")
        params.append(validate_email(email))
    if address is not None:
        updates.append("address = %s")
        params.append(validate_address(address))
    if not updates:
        raise ValidationError("Nothing to update.")

    params.append(customer_id)
    try:
        _, changed = execute(f"UPDATE customers SET {', '.join(updates)} WHERE customer_id = %s", tuple(params))
    except DuplicateEntryError:
        raise ValidationError("Another customer already uses this phone number or email.")
    return changed > 0


def delete_customer(customer_id):
    """Delete a customer. Customers who still own accounts cannot be deleted."""
    customer_id = validate_id(customer_id, "Customer ID")
    if get_customer(customer_id) is None:
        raise ValidationError("Customer not found.")
    owned = fetch_one("SELECT COUNT(*) AS total FROM accounts WHERE customer_id = %s", (customer_id,))
    if owned["total"] > 0:
        raise ValidationError("This customer still has accounts. Deactivate/remove the accounts first.")
    _, deleted = execute("DELETE FROM customers WHERE customer_id = %s", (customer_id,))
    return deleted > 0
