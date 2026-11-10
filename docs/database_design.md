# Database design (banking_db)

## Entities and relationships
* One **customer** has many **accounts** (customers 1 : N accounts).
* One **account** has many **transactions** (accounts 1 : N transactions).

## customers
| Column | Type | Rules |
|--------|------|-------|
| customer_id | INT UNSIGNED | PK, auto increment |
| name | VARCHAR(100) | NOT NULL, CHECK length >= 2 |
| phone | VARCHAR(15) | NOT NULL, UNIQUE |
| email | VARCHAR(120) | NOT NULL, UNIQUE |
| address | VARCHAR(255) | optional |
| created_at | TIMESTAMP | default now |

## accounts
| Column | Type | Rules |
|--------|------|-------|
| account_id | INT UNSIGNED | PK |
| customer_id | INT UNSIGNED | FK -> customers, ON DELETE RESTRICT |
| account_number | VARCHAR(20) | NOT NULL, UNIQUE |
| account_type | VARCHAR(10) | CHECK in (SAVINGS, CURRENT) |
| balance | DECIMAL(14,2) | CHECK >= 0 |
| status | VARCHAR(10) | CHECK in (ACTIVE, INACTIVE) |
| created_at | TIMESTAMP | default now |

## transactions
| Column | Type | Rules |
|--------|------|-------|
| transaction_id | INT UNSIGNED | PK |
| account_id | INT UNSIGNED | FK -> accounts, ON DELETE RESTRICT |
| transaction_date | DATETIME | NOT NULL |
| transaction_type | VARCHAR(10) | CHECK in (DEPOSIT, WITHDRAWAL) |
| amount | DECIMAL(12,2) | CHECK > 0 |
| category | VARCHAR(50) | NOT NULL, default 'Other' |
| description | VARCHAR(255) | optional |
| reference_number | VARCHAR(30) | NOT NULL, UNIQUE |
| created_at | TIMESTAMP | default now |

## Normalization
All tables are in 3NF: every non-key column depends only on its table's primary key; customer details are
stored once in `customers`, not repeated in accounts or transactions. `accounts.balance` is a deliberate
stored (derived) value for speed; `balance_service` can verify it against the transactions.
Indexes: `(account_id, transaction_date)` and `category` on transactions.
