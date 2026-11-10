-- =====================================================================
-- Useful SQL queries (MEMBER 2). Run them one at a time in SQLyog
-- (select the query, then press F8).  Replace the values after '=' as needed.
-- =====================================================================
USE banking_db;

-- 1. All customers with the number of accounts they own
SELECT c.customer_id, c.name, c.email, COUNT(a.account_id) AS total_accounts
FROM customers c
LEFT JOIN accounts a ON a.customer_id = c.customer_id
GROUP BY c.customer_id, c.name, c.email
ORDER BY c.customer_id;

-- 2. Accounts with owner name and balance
SELECT a.account_id, a.account_number, c.name AS customer_name,
       a.account_type, a.balance, a.status
FROM accounts a
JOIN customers c ON c.customer_id = a.customer_id
ORDER BY a.account_id;

-- 3. Latest 20 transactions
SELECT t.transaction_id, t.transaction_date, a.account_number,
       t.transaction_type, t.amount, t.category, t.description
FROM transactions t
JOIN accounts a ON a.account_id = t.account_id
ORDER BY t.transaction_date DESC
LIMIT 20;

-- 4. Total deposits and withdrawals
SELECT
    COALESCE(SUM(CASE WHEN transaction_type = 'DEPOSIT'    THEN amount END), 0) AS total_deposits,
    COALESCE(SUM(CASE WHEN transaction_type = 'WITHDRAWAL' THEN amount END), 0) AS total_withdrawals
FROM transactions;

-- 5. Balance of each account calculated from its transactions
SELECT a.account_id, a.account_number, a.balance AS stored_balance,
       COALESCE(SUM(CASE WHEN t.transaction_type = 'DEPOSIT' THEN t.amount ELSE -t.amount END), 0) AS calculated_balance
FROM accounts a
LEFT JOIN transactions t ON t.account_id = a.account_id
GROUP BY a.account_id, a.account_number, a.balance;

-- 6. Monthly expenses
SELECT DATE_FORMAT(transaction_date, '%Y-%m') AS month, SUM(amount) AS total_expense
FROM transactions
WHERE transaction_type = 'WITHDRAWAL'
GROUP BY month
ORDER BY month;

-- 7. Category-wise expenses
SELECT category, SUM(amount) AS total_spent, COUNT(*) AS transactions
FROM transactions
WHERE transaction_type = 'WITHDRAWAL'
GROUP BY category
ORDER BY total_spent DESC;

-- 8. Largest 10 transactions
SELECT transaction_id, account_id, transaction_type, amount, category, transaction_date
FROM transactions
ORDER BY amount DESC
LIMIT 10;

-- 9. Search transactions by keyword
SELECT transaction_id, transaction_date, amount, category, description
FROM transactions
WHERE description LIKE '%shopping%' OR category LIKE '%shopping%';

-- 10. Withdrawals above 50,000 (simple large-transaction check)
SELECT transaction_id, account_id, amount, category, transaction_date
FROM transactions
WHERE transaction_type = 'WITHDRAWAL' AND amount > 50000;

-- 11. Accounts with more than 5 transactions on one day (busy days)
SELECT account_id, DATE(transaction_date) AS day, COUNT(*) AS transactions_that_day
FROM transactions
GROUP BY account_id, DATE(transaction_date)
HAVING COUNT(*) > 5;

-- 12. Average transaction amount per account
SELECT account_id, ROUND(AVG(amount), 2) AS average_amount
FROM transactions
GROUP BY account_id;
