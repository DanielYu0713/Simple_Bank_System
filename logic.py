# (更新的 logic.py)
import sqlite3
from datetime import datetime
from database import get_db_conn
from werkzeug.security import generate_password_hash, check_password_hash
import ai_services
import csv
import io
import exchange_rate 
import email_service 
import json 
import random 
import string 

DATE_FMT = "%Y-%m-%d"
MONTH_FMT = "%Y-%m"

def get_today_str():
    return datetime.now().strftime(DATE_FMT)

def get_this_month_str():
    return datetime.now().strftime(MONTH_FMT)

# --- Config (手動匯率) ---

def get_manual_rates():
    conn = get_db_conn()
    try:
        row = conn.execute("SELECT value FROM system_config WHERE key = 'manual_rates'").fetchone()
        if row:
            return json.loads(row['value'])
        return {}
    except Exception:
        return {}
    finally:
        conn.close()

def set_manual_rates(rates_dict):
    conn = get_db_conn()
    try:
        rates_json = json.dumps(rates_dict)
        conn.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES ('manual_rates', ?)", (rates_json,))
        conn.commit()
        return {"success": True}
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


# --- User & Auth ---

def get_all_customers():
    conn = get_db_conn()
    customers_rows = conn.execute("SELECT id, name, role, email FROM customers ORDER BY name").fetchall()
    conn.close()
    return [dict(row) for row in customers_rows]

def register_customer(name, password, amount, date_str, role='customer'):
    # (邏輯不變)
    if not name: return {"success": False, "error": "姓名不可為空"}
    if not password: return {"success": False, "error": "密碼不可為空"}
    if amount < 0: return {"success": False, "error": "初始金額不可為負"}
    if not date_str: date_str = get_today_str()

    hashed_password = generate_password_hash(password)
    conn = get_db_conn()
    try:
        cursor = conn.execute("SELECT id FROM customers WHERE name = ?", (name,))
        if cursor.fetchone():
            return {"success": False, "error": f"客戶 {name} 已存在"}

        conn.execute("BEGIN")
        
        cursor = conn.execute(
            "INSERT INTO customers (name, password, role, is_active) VALUES (?, ?, ?, ?)", 
            (name, hashed_password, role, 1) 
        )
        new_customer_id = cursor.lastrowid
        
        cursor = conn.execute(
            "INSERT INTO wallets (customer_id, currency, balance) VALUES (?, ?, ?)",
            (new_customer_id, 'TWD', amount)
        )
        new_wallet_id = cursor.lastrowid

        if amount > 0:
            conn.execute(
                "INSERT INTO transactions (wallet_id, date, type, amount, balance_after, note) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (new_wallet_id, date_str, '開戶', amount, amount, 'TWD 錢包開戶')
            )
        
        conn.commit()
        return {"success": True, "name": name, "twd_balance": amount}
    except sqlite3.Error as e:
        conn.rollback()
        return {"success": False, "error": f"資料庫錯誤: {e}"}
    finally:
        conn.close()

def check_login(name, password):
    conn = get_db_conn()
    row = conn.execute("SELECT * FROM customers WHERE name = ?", (name,)).fetchone()
    conn.close()
    if not row: return {"success": False, "error": "查無此帳號"}
    
    if not row['is_active']:
        return {"success": False, "error": "此帳號已被停權，請聯繫管理員"}

    if check_password_hash(row['password'], password):
        return {"success": True, "user": {"name": row['name'], "role": row['role']}}
    else:
        return {"success": False, "error": "密碼錯誤"}

def change_password(customer_name, old_password, new_password):
    if not old_password or not new_password:
        return {"success": False, "error": "新舊密碼不可為空"}
    
    conn = get_db_conn()
    try:
        row = conn.execute("SELECT password FROM customers WHERE name = ?", (customer_name,)).fetchone()
        if not row:
            return {"success": False, "error": "查無此帳號"}
        
        if not check_password_hash(row['password'], old_password):
            return {"success": False, "error": "舊密碼錯誤"}
            
        new_hashed_password = generate_password_hash(new_password)
        conn.execute("UPDATE customers SET password = ? WHERE name = ?", (new_hashed_password, customer_name))
        conn.commit()
        return {"success": True, "message": "密碼更新成功"}
    except sqlite3.Error as e:
        conn.rollback()
        return {"success": False, "error": f"資料庫錯誤: {e}"}
    finally:
        conn.close()


def get_my_wallets(customer_name):
    # (邏輯不變)
    conn = get_db_conn()
    try:
        rows = conn.execute(
            "SELECT w.currency, w.balance FROM wallets w "
            "JOIN customers c ON w.customer_id = c.id "
            "WHERE c.name = ?", 
            (customer_name,)
        ).fetchall()
        
        wallets = [dict(row) for row in rows]
        
        total_twd_value = 0.0
        twd_rates = exchange_rate.get_rates("TWD") 

        if twd_rates:
            for wallet in wallets:
                currency = wallet['currency']
                balance = wallet['balance']
                
                if currency == 'TWD':
                    total_twd_value += balance
                elif currency in twd_rates and twd_rates[currency] > 0:
                    twd_equivalent = balance / twd_rates[currency]
                    total_twd_value += twd_equivalent
        
        customer_row = conn.execute("SELECT email FROM customers WHERE name = ?", (customer_name,)).fetchone()
        email = customer_row['email'] if customer_row else None
        
        return {"success": True, "wallets": wallets, "email": email, "total_twd_value": total_twd_value}
    finally:
        conn.close()


def update_my_email(customer_name, email):
    # (邏輯不變)
    conn = get_db_conn()
    try:
        conn.execute("UPDATE customers SET email = ? WHERE name = ?", (email, customer_name))
        conn.commit()
        return {"success": True, "email": email}
    except sqlite3.Error as e: conn.rollback(); return {"success": False, "error": f"資料庫錯誤: {e}"}
    finally: conn.close()

# --- Wallet & Transaction ---

def _get_or_create_wallet(conn, customer_id, currency):
    # (邏輯不變)
    cursor = conn.execute(
        "SELECT id, balance FROM wallets WHERE customer_id = ? AND currency = ?",
        (customer_id, currency)
    )
    row = cursor.fetchone()
    
    if row:
        return row['id'], row['balance'] 
    else:
        cursor = conn.execute(
            "INSERT INTO wallets (customer_id, currency, balance) VALUES (?, ?, ?)",
            (customer_id, currency, 0.0)
        )
        new_wallet_id = cursor.lastrowid
        return new_wallet_id, 0.0 

def deposit_money(customer_name, amount, date_str, currency='TWD', note=None):
    # (邏輯不變)
    if amount <= 0: return {"success": False, "error": "金額必須 > 0"}
    if not date_str: date_str = get_today_str()

    conn = get_db_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        customer_row = conn.execute("SELECT id FROM customers WHERE name = ?", (customer_name,)).fetchone()
        if not customer_row:
            conn.rollback(); return {"success": False, "error": f"查無客戶 {customer_name}"}
        
        customer_id = customer_row['id']
        wallet_id, old_balance = _get_or_create_wallet(conn, customer_id, currency)
        new_balance = old_balance + amount
        
        final_note = note if note else f'{currency} 存款' 

        conn.execute("UPDATE wallets SET balance = ? WHERE id = ?", (new_balance, wallet_id))
        conn.execute(
            "INSERT INTO transactions (wallet_id, date, type, amount, balance_after, note) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (wallet_id, date_str, '存款', amount, new_balance, final_note)
        )
        
        conn.commit()
        return {"success": True, "name": customer_name, "new_balance": new_balance, "currency": currency}
    except sqlite3.Error as e: conn.rollback(); return {"success": False, "error": f"資料庫錯誤: {e}"}
    finally: conn.close()

def withdraw_money(customer_name, amount, date_str, currency='TWD', note=None):
    # (邏輯不變)
    if amount <= 0: return {"success": False, "error": "金額必須 > 0"}
    if not date_str: date_str = get_today_str()

    conn = get_db_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        customer_row = conn.execute("SELECT id FROM customers WHERE name = ?", (customer_name,)).fetchone()
        if not customer_row:
            conn.rollback(); return {"success": False, "error": f"查無客戶 {customer_name}"}
        
        customer_id = customer_row['id']
        wallet_row = conn.execute("SELECT id, balance FROM wallets WHERE customer_id = ? AND currency = ?", (customer_id, currency)).fetchone()
        
        if not wallet_row:
            conn.rollback(); return {"success": False, "error": f"您沒有 {currency} 錢包"}
        if wallet_row['balance'] < amount:
            conn.rollback(); return {"success": False, "error": f"{currency} 餘額不足"}

        wallet_id, old_balance = wallet_row['id'], wallet_row['balance']
        new_balance = old_balance - amount
        
        final_note = note if note else f'{currency} 提款' 

        conn.execute("UPDATE wallets SET balance = ? WHERE id = ?", (new_balance, wallet_id))
        conn.execute(
            "INSERT INTO transactions (wallet_id, date, type, amount, balance_after, note) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (wallet_id, date_str, '提款', -amount, new_balance, final_note)
        )
        
        conn.commit()
        return {"success": True, "name": customer_name, "new_balance": new_balance, "currency": currency}
    except sqlite3.Error as e: conn.rollback(); return {"success": False, "error": f"資料庫錯誤: {e}"}
    finally: conn.close()

def transfer_money(from_customer_name, to_customer_name, amount, date_str, currency='TWD', note=None):
    """ (*** (新) 修正備註邏輯 ***) """
    if from_customer_name == to_customer_name: return {"success": False, "error": "不能轉帳給自己"}
    if amount <= 0: return {"success": False, "error": "金額必須 > 0"}
    if not date_str: date_str = get_today_str()

    conn = get_db_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        
        from_customer = conn.execute("SELECT id, email FROM customers WHERE name = ?", (from_customer_name,)).fetchone()
        from_wallet = conn.execute("SELECT id, balance FROM wallets WHERE customer_id = ? AND currency = ?", (from_customer['id'], currency)).fetchone()
        if not from_wallet: conn.rollback(); return {"success": False, "error": f"轉出方沒有 {currency} 錢包"}
        if from_wallet['balance'] < amount: conn.rollback(); return {"success": False, "error": "餘額不足"}
            
        to_customer = conn.execute("SELECT id FROM customers WHERE name = ?", (to_customer_name,)).fetchone()
        if not to_customer: conn.rollback(); return {"success": False, "error": f"查無轉入帳號 {to_customer_name}"}
        to_wallet_id, to_old_balance = _get_or_create_wallet(conn, to_customer['id'], currency)

        from_wallet_id, from_new_balance = from_wallet['id'], from_wallet['balance'] - amount
        to_new_balance = to_old_balance + amount

        # (*** (新) 修正備註邏輯 (Req 3) ***)
        if note:
            from_note = f"{note} (轉給: {to_customer_name})"
            to_note = f"{note} (來自: {from_customer_name})"
        else:
            from_note = f'{currency} 轉給 {to_customer_name}'
            to_note = f'{currency} 來自 {from_customer_name}'
        # (*** 修正結束 ***)

        conn.execute("UPDATE wallets SET balance = ? WHERE id = ?", (from_new_balance, from_wallet_id))
        conn.execute(
            "INSERT INTO transactions (wallet_id, date, type, amount, balance_after, note) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (from_wallet_id, date_str, '轉出', -amount, from_new_balance, from_note)
        )

        conn.execute("UPDATE wallets SET balance = ? WHERE id = ?", (to_new_balance, to_wallet_id))
        conn.execute(
            "INSERT INTO transactions (wallet_id, date, type, amount, balance_after, note) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (to_wallet_id, date_str, '轉入', amount, to_new_balance, to_note)
        )

        conn.commit()
        
        if from_customer['email']:
            email_service.send_transfer_notification(
                from_customer['email'], from_customer_name, amount, currency, to_customer_name
            )

        return {"success": True, "new_balance": from_new_balance, "currency": currency}
    except sqlite3.Error as e: conn.rollback(); return {"success": False, "error": f"資料庫錯誤: {e}"}
    finally: conn.close()

def exchange_currency(customer_name, from_currency, to_currency, from_amount, date_str):
    # (邏輯不變)
    if from_currency == to_currency: return {"success": False, "error": "幣別相同，無需換匯"}
    if from_amount <= 0: return {"success": False, "error": "金額必須 > 0"}
    if not date_str: date_str = get_today_str()

    rate = None
    manual_rates = get_manual_rates()
    rate_key_direct = f"{from_currency}_{to_currency}"
    rate_key_reverse = f"{to_currency}_{from_currency}"

    if rate_key_direct in manual_rates:
        rate = manual_rates[rate_key_direct]
        print(f"[匯率] 使用手動匯率: {rate_key_direct}")
    elif rate_key_reverse in manual_rates and manual_rates[rate_key_reverse] > 0:
        rate = 1 / manual_rates[rate_key_reverse]
        print(f"[匯率] 使用反轉手動匯率: {rate_key_reverse}")

    if rate is None:
        print("[匯率] 使用 API 匯率")
        rates = exchange_rate.get_rates(from_currency)
        if not rates: return {"success": False, "error": "無法取得即時匯率"}
        rate = rates.get(to_currency)
        if not rate: return {"success": False, "error": f"無法取得 {from_currency} 到 {to_currency} 的匯率"}
    
    to_amount = from_amount * rate
    
    conn = get_db_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        
        customer = conn.execute("SELECT id, email FROM customers WHERE name = ?", (customer_name,)).fetchone()
        customer_id = customer['id']
        
        from_wallet = conn.execute("SELECT id, balance FROM wallets WHERE customer_id = ? AND currency = ?", (customer_id, from_currency)).fetchone()
        if not from_wallet: conn.rollback(); return {"success": False, "error": f"您沒有 {from_currency} 錢包"}
        if from_wallet['balance'] < from_amount: conn.rollback(); return {"success": False, "error": f"{from_currency} 餘額不足"}
        
        from_wallet_id, from_new_balance = from_wallet['id'], from_wallet['balance'] - from_amount
        
        to_wallet_id, to_old_balance = _get_or_create_wallet(conn, customer_id, to_currency)
        to_new_balance = to_old_balance + to_amount
        
        conn.execute("UPDATE wallets SET balance = ? WHERE id = ?", (from_new_balance, from_wallet_id))
        conn.execute(
            "INSERT INTO transactions (wallet_id, date, type, amount, balance_after, note, exchange_rate) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (from_wallet_id, date_str, '換匯轉出', -from_amount, from_new_balance, f'換成 {to_currency}', rate)
        )
        
        conn.execute("UPDATE wallets SET balance = ? WHERE id = ?", (to_new_balance, to_wallet_id))
        conn.execute(
            "INSERT INTO transactions (wallet_id, date, type, amount, balance_after, note, exchange_rate) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (to_wallet_id, date_str, '換匯轉入', to_amount, to_new_balance, f'來自 {from_currency}', rate)
        )
        
        conn.commit()
        
        if customer['email']:
            email_service.send_exchange_notification(
                customer['email'], from_amount, from_currency, to_amount, to_currency
            )
            
        return {
            "success": True, 
            "message": f"成功將 {from_amount} {from_currency} 兌換為 {to_amount:.2f} {to_currency}",
            "from_wallet_balance": from_new_balance,
            "to_wallet_balance": to_new_balance
        }
    except sqlite3.Error as e: conn.rollback(); return {"success": False, "error": f"資料庫錯誤: {e}"}
    finally: conn.close()


def get_my_transactions(customer_name, month=None):
    # (*** (新) 依使用者名稱查詢，而非 ID ***)
    conn = get_db_conn()
    base_sql = (
        "SELECT t.date, t.type, w.currency, t.amount, t.balance_after, t.note, t.exchange_rate "
        "FROM transactions t "
        "JOIN wallets w ON t.wallet_id = w.id "
        "JOIN customers c ON w.customer_id = c.id "
        "WHERE c.name = ? "
    )
    params = (customer_name,)
    
    if month:
        base_sql += "AND strftime('%Y-%m', t.date) = ? "
        params += (month,)
    
    base_sql += "ORDER BY t.date DESC, t.id DESC"
    
    rows = conn.execute(base_sql, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_my_transactions_as_csv(customer_name):
    # (邏輯不變)
    transactions = get_my_transactions(customer_name)
    if not transactions: return None
    
    output = io.StringIO()
    fieldnames = ['date', 'type', 'currency', 'amount', 'balance_after', 'note', 'exchange_rate']
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore') 
    
    writer.writeheader()
    writer.writerows(transactions)
    return output.getvalue()

# --- Analysis (Spending, Income) ---

def analyze_spending(customer_name, month=None, currency='TWD'):
    """ (*** (新) 修正 'ALL' 邏輯 (Req 4) 並修正 AI 分類邏輯 (Req 1, 2) ***) """
    conn = get_db_conn()
    
    sql = (
        "SELECT t.type, t.note FROM transactions t "
        "JOIN wallets w ON t.wallet_id = w.id "
        "JOIN customers c ON w.customer_id = c.id "
        "WHERE c.name = ? AND t.amount < 0 "
    )
    params = [customer_name]
    
    # (*** (新) 修正 'ALL' 邏輯 ***)
    if currency != 'ALL':
        sql += "AND w.currency = ? "
        params.append(currency)
    
    if month:
        sql += "AND strftime('%Y-%m', t.date) = ? "
        params.append(month)
    
    rows = conn.execute(sql, tuple(params)).fetchall()
    conn.close()
    
    analysis_unit = "TWD (總資產)" if currency == 'ALL' else currency
    
    if not rows:
        message = f"在 {month} 沒有可分析的 {analysis_unit} 支出紀錄" if month else f"沒有可分析的 {analysis_unit} 支出紀錄"
        return {"success": True, "summary": {}, "message": message, "suggestion": ""}

    summary = {}
    notes_for_ai = []

    # (*** (新) 修正分類邏輯 (Req 1, 2) ***)
    for row in rows:
        ttype = row['type']
        note = row['note']

        if note and note.startswith("管理員"):
            summary['管理員調整'] = summary.get('管理員調整', 0) + 1
        elif ttype == '換匯轉出':
            summary['換匯支出'] = summary.get('換匯支出', 0) + 1
        elif note:
            # 只要有備註 (無論是提款或轉出)，都交給 AI
            notes_for_ai.append(note)
        elif ttype == '轉出' and not note:
            summary['轉帳支出'] = summary.get('轉帳支出', 0) + 1
        elif ttype == '提款' and not note:
            summary['提款'] = summary.get('提款', 0) + 1
    # (*** 修正結束 ***)


    if notes_for_ai:
        categories = ["餐飲美食", "交通出行", "休閒娛樂", "網路購物", "帳單繳費", "家居生活", "其他"]
        ai_results = ai_services.categorize_spending(notes_for_ai, categories)
        
        if not ai_results:
            return {"success": False, "error": "AI 分析服務暫時無法連線"}

        temp_ai_summary = {category: 0 for category in categories}
        for i, note in enumerate(notes_for_ai):
            try:
                ai_result_for_tx = ai_results[i]
                top_category = ai_result_for_tx['labels'][0]
                temp_ai_summary[top_category] += 1
            except (IndexError, KeyError):
                temp_ai_summary["其他"] += 1
        
        for category, count in temp_ai_summary.items():
            if count > 0:
                summary[category] = summary.get(category, 0) + count

    summary_filtered = {k: v for k, v in summary.items() if v > 0}
    suggestion = ""
    if summary_filtered:
        try:
            spend_categories = {k: v for k, v in summary_filtered.items() if k not in ['轉帳支出', '換匯支出', '提款', '管理員調整']}
            if spend_categories:
                top_category = max(spend_categories, key=spend_categories.get)
                total_spend_count = sum(spend_categories.values())
                suggestion = f"💡 財務建議：在一般消費中，您本月在「{top_category}」上的支出次數最多 ({int(summary_filtered[top_category])} 次)，佔總 {int(total_spend_count)} 次消費的主要部分。"
            else:
                suggestion = f"💡 財務建議：您本月 {analysis_unit} 支出均為資產轉移，無一般消費紀錄。"
        except Exception as e:
            suggestion = "無法產生建議。"
            
    return {"success": True, "summary": summary_filtered, "message": f"(僅分析 {analysis_unit} 支出次數)", "suggestion": suggestion}


def analyze_income(customer_name, month=None, currency='TWD'):
    """ (*** (新) 修正 'ALL' 邏輯 (Req 4) ***) """
    conn = get_db_conn()
    sql = (
        "SELECT t.type, t.note, t.amount FROM transactions t "
        "JOIN wallets w ON t.wallet_id = w.id "
        "JOIN customers c ON w.customer_id = c.id "
        "WHERE c.name = ? AND t.amount > 0 "
    )
    params = [customer_name]

    # (*** (新) 修正 'ALL' 邏輯 ***)
    if currency != 'ALL':
        sql += "AND w.currency = ? "
        params.append(currency)

    if month:
        sql += "AND strftime('%Y-%m', t.date) = ? "
        params.append(month)
    
    rows = conn.execute(sql, tuple(params)).fetchall()
    conn.close()
    
    analysis_unit = "TWD (總資產)" if currency == 'ALL' else currency
    
    if not rows:
        message = f"在 {month} 沒有可分析的 {analysis_unit} 收入紀錄" if month else f"沒有可分析的 {analysis_unit} 收入紀錄"
        return {"success": True, "summary": {}, "message": message}

    summary = {}
    for row in rows:
        category = row['type']
        if row['note'] and row['note'].startswith("管理員"):
            category = '管理員調整'
        elif category == '存款':
            category = '存款收入'
        elif category == '轉入':
            category = '轉帳收入'
        elif category == '換匯轉入':
            category = '換匯收入'
        elif category == '開戶':
            category = '開戶金'
        else:
            category = '其他收入'
        
        summary[category] = summary.get(category, 0) + 1

    return {"success": True, "summary": summary, "message": f"(僅分析 {analysis_unit} 收入次數)"}

# --- Analysis (Cash Flow) ---

def _process_transactions_for_summary(rows, rate_to_twd=1.0, currency_prefix=""):
    """ (*** (新) 修正 AI 分類邏輯 (Req 1, 2) ***) """
    summary = {
        "total_income": 0.0, "total_spend": 0.0,
        "income_sources": {}, "spend_sources": {},
        "daily_flow": {}
    }
    notes_for_ai = [] 
    ai_spend_map = [] 
    
    for row in rows:
        date = row['date']
        ttype = row['type']
        amount = row['amount']
        note = row['note']
        
        amount_twd = amount * rate_to_twd
        
        if date not in summary["daily_flow"]:
            summary["daily_flow"][date] = {"income": 0, "spend": 0}

        if amount > 0:
            amount_abs_twd = abs(amount_twd)
            summary["total_income"] += amount_abs_twd
            summary["daily_flow"][date]["income"] += amount_abs_twd
            
            if note and note.startswith("管理員"):
                source_name = '管理員調整'
            elif ttype in ['存款', '開戶']:
                source_name = ttype
            elif ttype == '轉入':
                source_name = '轉帳收入'
            elif ttype == '換匯轉入':
                source_name = '換匯收入'
            else:
                source_name = '其他收入'
            summary["income_sources"][source_name] = summary["income_sources"].get(source_name, 0) + amount_abs_twd
        
        elif amount < 0:
            amount_abs_twd = abs(amount_twd)
            summary["total_spend"] += amount_abs_twd
            summary["daily_flow"][date]["spend"] += amount_abs_twd

            # (*** (新) 修正分類邏輯 (Req 1, 2) ***)
            source_name = None
            if note and note.startswith("管理員"):
                source_name = '管理員調整'
            elif ttype == '換匯轉出':
                source_name = '換匯支出'
            elif note:
                # 只要有備註 (無論是提款或轉出)，都交給 AI
                notes_for_ai.append(note)
                ai_spend_map.append({"note": note, "amount": amount_abs_twd})
            elif ttype == '轉出' and not note:
                source_name = '轉帳支出'
            elif ttype == '提款' and not note:
                source_name = '提款 (無備註)'
            else:
                source_name = '其他支出 (無備註)'
            # (*** 修正結束 ***)
            
            if source_name:
                summary["spend_sources"][source_name] = summary["spend_sources"].get(source_name, 0) + amount_abs_twd

    # 4. 呼叫 AI 服務
    if notes_for_ai:
        categories = ["餐飲美食", "交通出行", "休閒娛樂", "網路購物", "帳單繳費", "家居生活", "其他"]
        ai_results = ai_services.categorize_spending(notes_for_ai, categories)
        
        if ai_results:
            for i, spend_item in enumerate(ai_spend_map):
                try:
                    top_category = ai_results[i]['labels'][0]
                    summary["spend_sources"][top_category] = summary["spend_sources"].get(top_category, 0) + spend_item['amount']
                except (IndexError, KeyError):
                    summary["spend_sources"]["其他"] = summary["spend_sources"].get("其他", 0) + spend_item['amount']
        else:
            for spend_item in ai_spend_map:
                 summary["spend_sources"]["其他 (AI分析失敗)"] = summary["spend_sources"].get("其他 (AI分析失敗)", 0) + spend_item['amount']

    return summary


def analyze_cash_flow(customer_name, month=None, currency='TWD'):
    # (邏輯不變)
    conn = get_db_conn()
    try:
        customer_id = conn.execute("SELECT id FROM customers WHERE name = ?", (customer_name,)).fetchone()['id']
        
        final_summary = {
            "total_income": 0.0, "total_spend": 0.0,
            "income_sources": {}, "spend_sources": {},
            "daily_flow": {}, "cumulative_flow": {}
        }
        
        wallets_to_analyze = []
        
        if currency == 'ALL':
            rows = conn.execute("SELECT id, currency FROM wallets WHERE customer_id = ?", (customer_id,)).fetchall()
            wallets_to_analyze = [dict(row) for row in rows]
        else:
            row = conn.execute("SELECT id, currency FROM wallets WHERE customer_id = ? AND currency = ?", (customer_id, currency)).fetchone()
            if row:
                wallets_to_analyze = [dict(row)]

        if not wallets_to_analyze:
            return {"success": True, "summary": {}, "suggestion": f"沒有 {currency} 錢包"}
            
        twd_rates = None
        if currency == 'ALL':
            twd_rates = exchange_rate.get_rates("TWD")
            if not twd_rates:
                return {"success": False, "error": "無法取得 'ALL' 分析所需的 TWD 匯率"}

        for wallet in wallets_to_analyze:
            wallet_id = wallet['id']
            curr = wallet['currency']
            
            rate_to_twd = 1.0
            if currency == 'ALL' and curr != 'TWD':
                if curr not in twd_rates or twd_rates[curr] <= 0:
                    continue 
                rate_to_twd = 1.0 / twd_rates[curr]
            
            sql = "SELECT date, type, amount, note FROM transactions WHERE wallet_id = ? "
            params = (wallet_id,)
            if month:
                sql += "AND strftime('%Y-%m', date) = ? "
                params += (month,)
            sql += "ORDER BY date ASC"
            
            rows = conn.execute(sql, params).fetchall()
            if not rows:
                continue
            
            summary_part = _process_transactions_for_summary(rows, rate_to_twd, currency_prefix=f"({curr}) ")
            
            final_summary["total_income"] += summary_part["total_income"]
            final_summary["total_spend"] += summary_part["total_spend"]
            
            for k, v in summary_part["income_sources"].items():
                final_summary["income_sources"][k] = final_summary["income_sources"].get(k, 0) + v
            for k, v in summary_part["spend_sources"].items():
                final_summary["spend_sources"][k] = final_summary["spend_sources"].get(k, 0) + v
            for k, v in summary_part["daily_flow"].items():
                if k not in final_summary["daily_flow"]:
                    final_summary["daily_flow"][k] = {"income": 0, "spend": 0}
                final_summary["daily_flow"][k]["income"] += v["income"]
                final_summary["daily_flow"][k]["spend"] += v["spend"]

        if not final_summary["daily_flow"]:
             return {"success": True, "summary": {}, "suggestion": f"沒有 {currency} 交易紀錄"}

        running_income = 0.0
        running_spend = 0.0
        sorted_dates = sorted(final_summary["daily_flow"].keys())
        for date in sorted_dates:
            daily = final_summary["daily_flow"][date]
            running_income += daily["income"]
            running_spend += daily["spend"]
            final_summary["cumulative_flow"][date] = {
                "income": running_income,
                "spend": running_spend
            }

        suggestion = ""
        analysis_unit = "TWD (總資產)" if currency == 'ALL' else currency
        try:
            spend_categories = {
                k: v for k, v in final_summary["spend_sources"].items() 
                if k not in ['轉帳支出', '換匯支出', '提款 (無備註)', '其他支出 (無備註)', '管理員調整']
            }
            if spend_categories:
                top_category = max(spend_categories, key=spend_categories.get)
                top_amount = spend_categories[top_category]
                total_spend = final_summary["total_spend"]
                if total_spend > 0:
                    percent = (top_amount / total_spend) * 100
                    suggestion = f"💡 財務建議：在 {analysis_unit} 支出中，您在「{top_category}」上的支出總額最高 (${top_amount:,.2f})，佔總支出的 {percent:.1f}%。"
            elif final_summary["total_spend"] > 0:
                 suggestion = f"💡 財務建議：您本月 {analysis_unit} 支出均為資產轉移，無 AI 可分析的一般消費紀錄。"
            else:
                suggestion = f"💡 財務建議：本期無 {analysis_unit} 支出紀錄。"
        except Exception as e:
            suggestion = "無法產生建議。"

        return {"success": True, "summary": final_summary, "suggestion": suggestion}
        
    except Exception as e:
        print(f"analyze_cash_flow 錯誤: {e}")
        return {"success": False, "error": str(e), "suggestion": "分析時發生錯誤"}
    finally:
        conn.close()

# --- Analysis (Budget) ---

CATEGORIES = ["餐飲美食", "交通出行", "休閒娛樂", "網路購物", "帳單繳費", "家居生活", "其他"]

def get_budgets(customer_name, month, currency):
    # (邏輯不變)
    conn = get_db_conn()
    customer_id = conn.execute("SELECT id FROM customers WHERE name = ?", (customer_name,)).fetchone()['id']
    
    rows = conn.execute(
        "SELECT category, amount FROM budgets WHERE customer_id = ? AND month = ? AND currency = ?",
        (customer_id, month, currency)
    ).fetchall()
    
    budgets = {category: 0 for category in CATEGORIES}
    for row in rows:
        budgets[row['category']] = row['amount']
        
    conn.close()
    return {"success": True, "budgets": budgets, "categories": CATEGORIES}

def set_budget(customer_name, month, currency, category, amount):
    # (邏輯不變)
    conn = get_db_conn()
    try:
        customer_id = conn.execute("SELECT id FROM customers WHERE name = ?", (customer_name,)).fetchone()['id']
        conn.execute(
            "INSERT OR REPLACE INTO budgets (customer_id, month, currency, category, amount) "
            "VALUES (?, ?, ?, ?, ?)",
            (customer_id, month, currency, category, amount)
        )
        conn.commit()
        return {"success": True}
    except sqlite3.Error as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def get_spending_vs_budget(customer_name, month, currency):
    # (邏輯不變)
    budget_data = get_budgets(customer_name, month, currency)['budgets']
    spend_data = analyze_cash_flow(customer_name, month, currency)
    
    if not spend_data['success']:
        return spend_data 
        
    spend_sources = spend_data.get('summary', {}).get('spend_sources', {})
    
    comparison = []
    total_budget = 0
    total_spent = 0
    
    for category in CATEGORIES:
        budget = budget_data.get(category, 0)
        spent = spend_sources.get(category, 0) # AI 分類過的支出
        comparison.append({
            "category": category,
            "budget": budget,
            "spent": spent
        })
        total_budget += budget
        total_spent += spent
        
    return {"success": True, "comparison": comparison, "total_budget": total_budget, "total_spent": total_spent}


# --- Admin Functions ---

def get_system_stats():
    """ (*** (新) 擴充: 回傳各幣別總資產 (Req 5B) ***) """
    conn = get_db_conn()
    try:
        total_users = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        active_users = conn.execute("SELECT COUNT(*) FROM customers WHERE is_active = 1").fetchone()[0]
        
        wallets = conn.execute("SELECT currency, balance FROM wallets").fetchall()
        twd_rates = exchange_rate.get_rates("TWD")
        
        # (*** (新) 各幣別統計 ***)
        assets_by_currency = {}
        total_assets_twd = 0.0
        
        for w in wallets:
            assets_by_currency[w['currency']] = assets_by_currency.get(w['currency'], 0) + w['balance']

        if twd_rates:
            for currency, balance in assets_by_currency.items():
                if currency == 'TWD':
                    total_assets_twd += balance
                elif currency in twd_rates and twd_rates[currency] > 0:
                    total_assets_twd += balance / twd_rates[currency]
                    
        return {"success": True, "stats": {
            "total_users": total_users,
            "active_users": active_users,
            "total_assets_twd": total_assets_twd,
            "assets_by_currency": assets_by_currency # (*** (新) ***)
        }}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()

def admin_get_all_users():
    # (邏輯不變)
    conn = get_db_conn()
    rows = conn.execute("SELECT id, name, email, role, is_active FROM customers ORDER BY id").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def admin_get_user_details(user_id):
    """ (*** (新) 修正: 不再主動載入交易紀錄 (Req 5A) ***) """
    conn = get_db_conn()
    try:
        user = conn.execute("SELECT id, name, email, role, is_active FROM customers WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return {"success": False, "error": "查無此人"}
        
        user_data = dict(user)
        # 借用現有函式
        wallets_data = get_my_wallets(user_data['name'])
        
        user_data['wallets'] = wallets_data.get('wallets', [])
        # (*** 移除 transactions_data 的載入 ***)
        
        return {"success": True, "user_data": user_data}
    finally:
        conn.close()

def admin_update_user(user_id, email, role, is_active):
    # (邏輯不變)
    conn = get_db_conn()
    try:
        conn.execute(
            "UPDATE customers SET email = ?, role = ?, is_active = ? WHERE id = ?",
            (email, role, is_active, user_id)
        )
        conn.commit()
        return {"success": True}
    except sqlite3.Error as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()
        
def admin_reset_password(user_id):
    # (邏輯不變)
    conn = get_db_conn()
    try:
        user = conn.execute("SELECT name, email FROM customers WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return {"success": False, "error": "查無此人"}

        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        new_hashed_password = generate_password_hash(new_password)
        
        conn.execute("UPDATE customers SET password = ? WHERE id = ?", (new_hashed_password, user_id))
        conn.commit()
        
        if user['email']:
            email_service.send_password_reset_notification(user['email'], new_password)
            
        return {"success": True, "new_password": new_password}
    except sqlite3.Error as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    finally:
        conn.close()
        
def admin_manual_adjustment(admin_name, user_id, currency, amount, note):
    # (邏輯不變)
    conn = get_db_conn()
    try:
        user = conn.execute("SELECT name FROM customers WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return {"success": False, "error": "查無此人"}
        
        user_name = user['name']
        date_str = get_today_str()
        
        if amount > 0:
            result = deposit_money(user_name, amount, date_str, currency, note=note)
        elif amount < 0:
            result = withdraw_money(user_name, abs(amount), date_str, currency, note=note)
        else:
            return {"success": False, "error": "金額不可為 0"}
            
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()