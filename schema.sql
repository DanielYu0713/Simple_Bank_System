-- (新的 schema.sql)
-- 刪除舊資料表 (如果存在)
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS wallets;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS budgets;
DROP TABLE IF EXISTS system_config;

-- 客戶表 (*** 新增 is_active ***)
CREATE TABLE customers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'customer', -- 'customer' 或 'admin'
  email TEXT,
  is_active BOOLEAN NOT NULL DEFAULT 1 -- (*** 新增 ***) 1=啟用, 0=停權
);

-- 錢包表 (與之前相同)
CREATE TABLE wallets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INTEGER NOT NULL,
  currency TEXT NOT NULL, -- 'TWD', 'USD' 等
  balance REAL NOT NULL DEFAULT 0,
  FOREIGN KEY (customer_id) REFERENCES customers (id)
);

-- 交易表 (與之前相同)
CREATE TABLE transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  wallet_id INTEGER NOT NULL,
  date TEXT NOT NULL,
  type TEXT NOT NULL, -- '開戶', '存款', '提款', '轉出', '轉入', '換匯轉出', '換匯轉入'
  amount REAL NOT NULL, -- 正數為入帳, 負數為出帳
  balance_after REAL NOT NULL, -- 交易後餘額
  note TEXT, -- 備註
  exchange_rate REAL, -- 匯率 (僅換匯時)
  FOREIGN KEY (wallet_id) REFERENCES wallets (id)
);

-- (*** (新) 預算表 ***)
CREATE TABLE budgets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INTEGER NOT NULL,
  month TEXT NOT NULL, -- 格式 'YYYY-MM'
  currency TEXT NOT NULL,
  category TEXT NOT NULL,
  amount REAL NOT NULL,
  FOREIGN KEY (customer_id) REFERENCES customers (id),
  UNIQUE(customer_id, month, currency, category)
);

-- (*** (新) 系統設定表 ***)
CREATE TABLE system_config (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- 插入一筆預設資料 (例如手動匯率)
INSERT INTO system_config (key, value) VALUES ('manual_rates', '{}');