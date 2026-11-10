# Database (Member 2)

Database name: **banking_db** (MySQL 8.0.16 or newer, because older versions ignore CHECK constraints).

| File | Purpose |
|------|---------|
| `schema.sql` | Creates the database, the 3 tables, keys and constraints |
| `sample_data.sql` | Fictional data: 10 customers, 12 accounts, 300+ transactions (a few are intentionally unusual) |
| `queries.sql` | Example SQL queries for analysis and checking |

## Run it in SQLyog
1. Connect to your MySQL server (File -> New Connection).
2. File -> Open -> `schema.sql`, then press **Ctrl+Shift+F9** (Execute all queries).
3. File -> Open -> `sample_data.sql`, then press **Ctrl+Shift+F9**.
4. Press F5 to refresh the object browser and check that `banking_db` has 3 tables.

## Tables
```
customers (1) ----< accounts (1) ----< transactions
```
* `customers.phone` and `customers.email` are UNIQUE.
* `accounts.account_number` is UNIQUE, `balance >= 0`, type is SAVINGS/CURRENT, status is ACTIVE/INACTIVE.
* `transactions.amount > 0`, type is DEPOSIT/WITHDRAWAL, `reference_number` is UNIQUE.
* Foreign keys use `ON DELETE RESTRICT`: a customer with accounts, or an account with transactions, cannot be deleted by mistake.

`accounts.balance` is kept in sync with the transactions by the Python backend (`backend/balance_service.py`).
