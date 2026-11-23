-- E-commerce relational schema (PostgreSQL)

DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id  VARCHAR(20)  PRIMARY KEY,
    full_name    VARCHAR(120) NOT NULL,
    email        VARCHAR(160) NOT NULL UNIQUE,
    city         VARCHAR(80)  NOT NULL,
    country      VARCHAR(80)  NOT NULL,
    signup_date  VARCHAR(10)  NOT NULL
);

CREATE TABLE orders (
    order_id     VARCHAR(20)    PRIMARY KEY,
    customer_id  VARCHAR(20)    NOT NULL REFERENCES customers (customer_id),
    order_date   VARCHAR(10)    NOT NULL,
    product_name VARCHAR(120)   NOT NULL,
    category     VARCHAR(60)    NOT NULL,
    quantity     INTEGER        NOT NULL CHECK (quantity > 0),
    unit_price   NUMERIC(10, 2) NOT NULL CHECK (unit_price >= 0),
    total_amount NUMERIC(12, 2) NOT NULL,
    status       VARCHAR(20)    NOT NULL
);

CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_orders_date ON orders (order_date);
