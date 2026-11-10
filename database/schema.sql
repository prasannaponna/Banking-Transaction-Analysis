-- =====================================================================
-- Banking Transaction Analysis System - Database Schema   (MEMBER 2)
-- Requires MySQL 8.0.16+ (CHECK constraints are enforced from 8.0.16).
-- Run this file first in SQLyog (Ctrl+Shift+F9 = execute all queries).
-- WARNING: the DROP TABLE lines below delete existing data.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS banking_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE banking_db;

DROP TABLE IF EXISTS deleted_accounts;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS customers;

-- ---------------------------------------------------------------------
-- customers: one row per bank customer
-- ---------------------------------------------------------------------
CREATE TABLE customers (
    customer_id  INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    name         VARCHAR(100)  NOT NULL,
    phone        VARCHAR(15)   NOT NULL,
    email        VARCHAR(120)  NOT NULL,
    address      VARCHAR(255)  NULL,
    created_at   TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customer_id),
    UNIQUE KEY uq_customers_phone (phone),
    UNIQUE KEY uq_customers_email (email),
    CONSTRAINT chk_customers_name CHECK (CHAR_LENGTH(TRIM(name)) >= 2)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- accounts: one customer can own many accounts (1 : N)
-- ---------------------------------------------------------------------
CREATE TABLE accounts (
    account_id      INT UNSIGNED   NOT NULL AUTO_INCREMENT,
    customer_id     INT UNSIGNED   NOT NULL,
    account_number  VARCHAR(20)    NOT NULL,
    account_type    VARCHAR(10)    NOT NULL,
    balance         DECIMAL(14,2)  NOT NULL DEFAULT 0.00,
    created_at      TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status          VARCHAR(10)    NOT NULL DEFAULT 'ACTIVE',
    PRIMARY KEY (account_id),
    UNIQUE KEY uq_accounts_number (account_number),
    CONSTRAINT fk_accounts_customer
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_accounts_type    CHECK (account_type IN ('SAVINGS', 'CURRENT')),
    CONSTRAINT chk_accounts_status  CHECK (status IN ('ACTIVE', 'INACTIVE')),
    CONSTRAINT chk_accounts_balance CHECK (balance >= 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- transactions: one account can have many transactions (1 : N)
-- ---------------------------------------------------------------------
CREATE TABLE transactions (
    transaction_id    INT UNSIGNED   NOT NULL AUTO_INCREMENT,
    account_id        INT UNSIGNED   NOT NULL,
    transaction_date  DATETIME       NOT NULL,
    transaction_type  VARCHAR(10)    NOT NULL,
    amount            DECIMAL(12,2)  NOT NULL,
    category          VARCHAR(50)    NOT NULL DEFAULT 'Other',
    description       VARCHAR(255)   NULL,
    reference_number  VARCHAR(30)    NOT NULL,
    created_at        TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (transaction_id),
    UNIQUE KEY uq_transactions_reference (reference_number),
    KEY idx_transactions_account_date (account_id, transaction_date),
    KEY idx_transactions_category (category),
    CONSTRAINT fk_transactions_account
        FOREIGN KEY (account_id) REFERENCES accounts (account_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_transactions_type   CHECK (transaction_type IN ('DEPOSIT', 'WITHDRAWAL')),
    CONSTRAINT chk_transactions_amount CHECK (amount > 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- deleted_accounts: recycle bin. When an account is deleted, a copy of
-- the account and its transactions (JSON) is stored here first, so it can
-- be restored later or purged permanently.
-- ---------------------------------------------------------------------
CREATE TABLE deleted_accounts (
    id                 INT UNSIGNED   NOT NULL AUTO_INCREMENT,
    account_id         INT UNSIGNED   NOT NULL,
    customer_id        INT UNSIGNED   NOT NULL,
    customer_name      VARCHAR(100)   NOT NULL,
    account_number     VARCHAR(20)    NOT NULL,
    account_type       VARCHAR(10)    NOT NULL,
    balance            DECIMAL(14,2)  NOT NULL,
    status             VARCHAR(10)    NOT NULL,
    account_created_at DATETIME       NULL,
    transaction_count  INT UNSIGNED   NOT NULL DEFAULT 0,
    transactions_json  LONGTEXT       NULL,
    deleted_at         TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    restored_at        TIMESTAMP      NULL DEFAULT NULL,
    PRIMARY KEY (id),
    KEY idx_deleted_accounts_deleted_at (deleted_at)
) ENGINE=InnoDB;
