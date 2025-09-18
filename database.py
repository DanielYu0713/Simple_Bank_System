import sqlite3
import os

DATABASE_NAME = 'bank.db' # 資料庫將被存在這個檔案中

def get_db_conn():
    """獲取一個資料庫連線物件，並設定為字典模式"""
    conn = sqlite3.connect(DATABASE_NAME)
    # 讓查詢結果可以像字典一樣用欄位名稱取值
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """讀取 schema.sql 檔案並執行它來建立資料表"""
    if os.path.exists(DATABASE_NAME):
        print(f"資料庫 {DATABASE_NAME} 已存在，將會刪除重建。")
        os.remove(DATABASE_NAME)
        
    conn = get_db_conn()
    with open('schema.sql', 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("資料庫初始化完成。")