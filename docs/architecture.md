# Architecture

```
dashboard/app.py ──> dashboard/pages/*.py ──> dashboard/components/{charts,tables}.py
                           │                          │
                           ├──> analysis/*  (Pandas, no SQL)
                           └──> backend/*   (services, all SQL)
                                      └──> backend/db_connection.py ──> MySQL banking_db
utils/validators.py and utils/helpers.py are used by every layer (no dependencies on other layers).
```

## Rules
1. SQL lives only in `backend/` (and the `.sql` files). Always parameterized (`%s` + tuple).
2. `analysis/` works on DataFrames. Only `analysis.transaction_analysis.load_transactions()` calls the backend.
3. `dashboard/` never writes SQL. It catches `ValidationError` and `DatabaseError` and shows friendly messages.
4. Import direction: dashboard -> analysis -> backend -> utils. There are no circular imports
   (`transaction_service` does not import `account_service`; `account_service` imports `transaction_service`).

## Key design decisions
* **Balance** - `accounts.balance` is updated in the same DB transaction as every deposit/withdrawal
  (`SELECT ... FOR UPDATE` locks the row). `balance_service.calculate_balance()` recomputes it from the transactions.
* **Opening balance** - saved as a DEPOSIT, so balance = deposits - withdrawals always holds.
* **Accounts are deactivated, not deleted** - history stays intact.
* **Secrets** - only from environment variables / `.env`.
* **Errors** - raw MySQL errors are logged, never shown; users see short friendly messages.
