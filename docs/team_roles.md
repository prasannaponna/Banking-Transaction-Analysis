# Team roles

| Member | Role | Owns | Main tasks |
|--------|------|------|------------|
| 1 | Backend + Integration | `backend/`, `utils/`, `requirements.txt`, final merge | DB connection, CRUD, business rules, balance logic, merge branches, final testing |
| 2 | Database | `database/` | schema, constraints, sample data, SQL queries, database README |
| 3 | Data Analysis | `analysis/`, `tests/test_analysis.py` | Pandas/NumPy analysis, unusual transaction rules, report generation |
| 4 | UI + Visualization | `dashboard/` | Streamlit pages, Plotly charts, filters, tables, report downloads |

Shared: `docs/`, `README.md`, `tests/`. Each member writes tests for their own folder
(Member 1: `test_transactions.py`, `test_validators.py`; Member 2: `test_database.py`).

## Interfaces between members
* Member 4 calls `backend.*_service` functions and `analysis.*` functions.
* Member 3 receives DataFrames with the columns listed in `analysis/transaction_analysis.py`.
* Member 1's services return dictionaries / lists of dictionaries whose keys are the SQL column names.
* Table or column changes by Member 2 must be announced to Members 1 and 3.
