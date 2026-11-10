"""
Database connection helpers (MEMBER 1).

* Reads DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME from environment variables
  (or from the .env file in the project root). No password is stored in code.
* Real MySQL errors are written to the log only. The user sees a friendly message.
* Every query uses %s placeholders + a params tuple (parameterized SQL).
"""
import logging
import os
from contextlib import contextmanager
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error

# Load <project root>/.env if it exists
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Friendly database error. str(error) is safe to show to the user."""


class DatabaseConnectionError(DatabaseError):
    """MySQL is not reachable or the login details are wrong."""


class DuplicateEntryError(DatabaseError):
    """A UNIQUE value (phone, email, account number...) already exists."""


class RelatedRecordsError(DatabaseError):
    """The row is linked to other rows (foreign key), so it cannot be changed/deleted."""


def _translate_error(error):
    """Convert a raw MySQL error into one of our friendly errors."""
    logger.error("MySQL error %s: %s", getattr(error, "errno", None), error)
    errno = getattr(error, "errno", None)
    if errno == 1062:
        return DuplicateEntryError("A record with the same unique value already exists.")
    if errno in (1451, 1452):
        return RelatedRecordsError("This record is linked to other records, so the action is not allowed.")
    if errno in (2003, 2002, 2006, 2013, 1045, 1049, 1044):
        return DatabaseConnectionError(
            "Could not connect to the database. Check that MySQL is running and the .env settings are correct."
        )
    return DatabaseError("A database error occurred. Please try again.")


def get_connection():
    """Open a new MySQL connection using environment variables."""
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "banking_db"),
            connection_timeout=5,
        )
    except (Error, ValueError) as error:
        raise _translate_error(error) if isinstance(error, Error) else DatabaseConnectionError(
            "DB_PORT in the .env file must be a number."
        )


@contextmanager
def get_cursor(commit=False):
    """
    Yield a dictionary cursor. Rolls back automatically on any error.

        with get_cursor(commit=True) as cursor:
            cursor.execute("UPDATE ... WHERE id = %s", (5,))
    """
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True, buffered=True)
        yield cursor
        if commit:
            connection.commit()
    except Error as error:
        connection.rollback()
        raise _translate_error(error) from error
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def fetch_all(sql, params=None):
    """Run a SELECT and return a list of dictionaries."""
    with get_cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchall()


def fetch_one(sql, params=None):
    """Run a SELECT and return one dictionary (or None)."""
    with get_cursor() as cursor:
        cursor.execute(sql, params or ())
        return cursor.fetchone()


def execute(sql, params=None):
    """Run INSERT/UPDATE/DELETE, commit, and return (last_insert_id, affected_rows)."""
    with get_cursor(commit=True) as cursor:
        cursor.execute(sql, params or ())
        return cursor.lastrowid, cursor.rowcount


def check_connection():
    """Return True if the database can be reached (used at dashboard start-up)."""
    try:
        fetch_one("SELECT 1 AS ok")
        return True
    except DatabaseError:
        return False
