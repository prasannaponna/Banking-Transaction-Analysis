# Banking Transaction Analysis System

A college project: a modular Python + MySQL application to manage customers, accounts and
transactions, and to analyse them with Pandas and an interactive Streamlit / Plotly dashboard.

> **Not production banking software.** It is a learning project with fictional data, a demo-only
> login gate and simple rules. Do not use it with real financial information.

## Features
* **Landing page with the complete feature overview**, two login buttons and a separate plain login portal
* Customer, account and transaction management (create, read, update, delete/deactivate, search)
* Deposits and withdrawals with automatic balance updates; insufficient balance is rejected
* Transaction history, search and filters (date, type, category, amount, account)
* Analysis: totals, average, largest, statistics, monthly income/expense, category spending, income vs expense
* **Unusual transaction detection** - a simple rule-based feature with configurable thresholds
  (this is *not* a real banking fraud detection system)
* Interactive Plotly charts, KPI dashboard, CSV report export
* Input validation, parameterized SQL, environment variables for secrets, friendly error messages

## Technology stack
Python 3.10+, MySQL 8.0.16+, SQLyog, mysql-connector-python, Pandas, NumPy, Plotly, Streamlit,
python-dotenv, pytest, Git + GitHub.

## Architecture
```
Streamlit dashboard  ->  analysis (Pandas)  ->  backend (services)  ->  MySQL (banking_db)
      (Member 4)           (Member 3)             (Member 1)            (Member 2)
```
* `dashboard` only draws the UI and calls `backend` / `analysis`.
* `analysis` receives DataFrames, so it can be tested without a database.
* `backend` is the only layer that runs SQL (always with `%s` placeholders).

## Database structure
`customers (1) ---< accounts (1) ---< transactions` - see `docs/database_design.md`.

## Folder structure
```
banking-transaction-analysis/
├── README.md  requirements.txt  .gitignore  .env.example
├── database/    schema.sql  sample_data.sql  queries.sql  README.md
├── backend/     db_connection.py  customer_service.py  account_service.py
│                transaction_service.py  balance_service.py
├── analysis/    transaction_analysis.py  spending_analysis.py  monthly_analysis.py
│                unusual_transactions.py  report_generator.py
├── dashboard/   app.py  auth.py  landing.py  login.py  theme.py  assets/style.css
│                pages/(dashboard, customers, accounts, transactions, analysis, reports)
│                components/(charts.py, tables.py)
├── .streamlit/  config.toml  (base colours / font)
├── utils/       validators.py  helpers.py
├── tests/       test_database.py  test_transactions.py  test_analysis.py  test_validators.py
└── docs/        architecture.md  database_design.md  team_roles.md  project_workflow.md
```

## Team responsibilities
| Member | Role | Folder |
|--------|------|--------|
| 1 | Backend + integration + GitHub | `backend/`, `utils/` |
| 2 | Database | `database/` |
| 3 | Data analysis | `analysis/` |
| 4 | UI + visualization | `dashboard/` |

Details: `docs/team_roles.md`.

## Installation

### 1. MySQL
Install MySQL Server 8.0.16 or newer (older versions ignore CHECK constraints) and remember the
`root` password you set.

### 2. Create the database with SQLyog
1. Open SQLyog -> **New** connection: host `localhost`, user `root`, your password, port `3306` -> Connect.
2. **File -> Open** `database/schema.sql` -> press **Ctrl+Shift+F9** (execute all queries).
3. **File -> Open** `database/sample_data.sql` -> press **Ctrl+Shift+F9**.
4. Right-click the connection -> *Refresh*. `banking_db` should have 3 tables with
   10 customers, 12 accounts and 364 transactions.

### 3. Python environment
```bash
cd banking-transaction-analysis
python -m venv venv
```
Activate it:
```bash
# Windows (Command Prompt)
venv\Scripts\activate
# Windows (PowerShell)
venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate
```
Install packages:
```bash
pip install -r requirements.txt
```

### 4. Configure `.env`
```bash
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```
Edit `.env` and set your own MySQL password:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=banking_db
```
The `.env` file is ignored by Git, so your password is never uploaded.

## How to run
Run from the project root folder:
```bash
streamlit run dashboard/app.py
```
The browser opens at http://localhost:8501.

The first screen is the landing page. It lists the features and the analysis and reporting
capabilities. Use the **Open login portal** button to open the separate login page, then sign in
to enter the dashboard.

### Demo login accounts
| Username | Password | Dashboard role |
|----------|----------|----------------|
| `admin` | `admin@123` | Administrator |
| `member1` | `backend` | Member 1 - Backend |
| `member2` | `database` | Member 2 - Database |
| `member3` | `analysis` | Member 3 - Data Analysis |
| `member4` | `dashboard` | Member 4 - Dashboard |
| `viewer` | `viewer` | Viewer |

The account's role is shown in the dashboard; it does not restrict pages.
These credentials are for the college demo only and are not production authentication.

## How to use the dashboard
* **Landing / login** - read the feature overview, open the separate plain login page, sign in with
  a demo account and use **Log out** in the sidebar to return to the landing page.
* **Dashboard** - KPI cards, monthly spending, income vs expense, category chart, recent
  transactions, unusual transaction alerts. Use the sidebar filters (account, date range, type, category).
* **Customers / Accounts** - three tabs each: view & search, add/open, edit/delete (accounts are deactivated, not deleted).
* **Transactions** - filter and search, add a deposit/withdrawal, edit or delete a transaction.
  Withdrawals bigger than the balance are rejected.
* **Analysis** - statistics, monthly, category, income vs expense and unusual transactions.
  Change the unusual-transaction thresholds in the sidebar.
* **Reports** - choose a report and click *Download CSV*.

The sample data deliberately contains unusual transactions (for example a ₹75,000 shopping
withdrawal on account 1000000001 and 7 quick withdrawals on account 1000000003 on 25 Sep 2026).

## Unusual transaction detection (rules)
1. Amount is more than *N* standard deviations above the account's normal amount for that type (default 3).
2. Amount is at least the configured limit (default ₹50,000).
3. Too many transactions on one account in a short time (default 5 within 60 minutes).

It only highlights transactions worth a second look. It is not fraud detection.

## Git workflow
See `docs/project_workflow.md`. Short version:
```bash
git clone <repo-url>
git checkout -b backend-member1        # your own branch
git add .
git commit -m "Add transaction service"
git push -u origin backend-member1
# open a Pull Request on GitHub -> review -> merge into main
```

## Testing
```bash
pytest -v
```
`test_validators.py` and `test_analysis.py` need no database. `test_database.py` and
`test_transactions.py` need MySQL + `.env`; they are skipped automatically if MySQL is unreachable.
They create temporary customers/accounts and delete them afterwards.

## Future improvements
Production authentication with password hashing and role-based authorization, transfers between
accounts, budgets and alerts by e-mail, PDF reports, pagination for large tables, machine-learning
based anomaly detection, Docker setup.

## Limitations
* Authentication is demo-only: credentials are hard-coded in `dashboard/auth.py`, and the role
  selector does not enforce page-level permissions.
* Single currency (₹); deposits/withdrawals only (no transfers).
* Editing/deleting old transactions recalculates the balance but does not check the balance at every past date.
* Unusual transaction detection is simple and rule-based.
* Opening balances are stored as DEPOSIT transactions (category "Opening Balance"), so they appear in income totals.
* Not production-ready banking software.

## Theme / customising the look
* `dashboard/assets/style.css` - all custom CSS (colours are variables at the top, in `:root`).
* `dashboard/theme.py` - HTML helpers: `page_header()`, `kpi_card()`, `section_title()`.
* `.streamlit/config.toml` - Streamlit's base theme colours.
* `dashboard/components/charts.py` - shared Plotly styling in `_style()` and `PALETTE`.
