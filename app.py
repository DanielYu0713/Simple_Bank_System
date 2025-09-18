# (更新的 app.py)
from flask import Flask, request, jsonify, render_template, session, make_response, redirect, url_for
from flask_session import Session
import click
import database
import logic
import os
from dotenv import load_dotenv
import exchange_rate 
from functools import wraps 
import json 

load_dotenv()
app = Flask(__name__)

app.config["SECRET_KEY"] = os.urandom(24) 
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

# --- Admin Decorator ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_role") != 'admin':
            return jsonify({"error": "權限不足"}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- User API ---

@app.route('/api/register', methods=['POST'])
def api_register():
    # (邏輯不變)
    data = request.json
    result = logic.register_customer(
        data.get('name'), data.get('password'), 
        float(data.get('amount', 0)), logic.get_today_str(), role='customer'
    )
    return jsonify(result)

@app.route('/api/login', methods=['POST'])
def api_login():
    # (邏輯不變)
    data = request.json
    result = logic.check_login(data.get('name'), data.get('password'))
    if result["success"]:
        session["user_name"] = result["user"]["name"]
        session["user_role"] = result["user"]["role"]
    return jsonify(result)

@app.route('/api/logout', methods=['POST'])
def api_logout():
    # (邏輯不變)
    session.clear()
    return jsonify({"success": True, "message": "已登出"})

@app.route('/api/session', methods=['GET'])
def api_check_session():
    # (邏輯不變)
    if "user_name" in session:
        name = session["user_name"]
        result = logic.get_my_wallets(name) 
        
        if result["success"]:
            is_admin = session.get("user_role") == 'admin' 
            return jsonify({
                "is_logged_in": True,
                "user_name": name,
                "user_role": session.get("user_role"),
                "is_admin": is_admin, 
                "wallets": result["wallets"], 
                "email": result["email"],
                "total_twd_value": result.get("total_twd_value", 0) 
            })
    
    return jsonify({"is_logged_in": False})

# --- Bank API (User) ---

@app.route('/api/deposit', methods=['POST'])
def api_deposit():
    if "user_name" not in session: return jsonify({"error": "尚未登入"}), 401
    name = session["user_name"] 
    data = request.json
    result = logic.deposit_money(
        name, float(data.get('amount', 0)),
        data.get('date') or logic.get_today_str(),
        data.get('currency', 'TWD'),
        note=data.get('note')
    )
    return jsonify(result)

@app.route('/api/withdraw', methods=['POST'])
def api_withdraw():
    if "user_name" not in session: return jsonify({"error": "尚未登入"}), 401
    name = session["user_name"] 
    data = request.json
    result = logic.withdraw_money(
        name, float(data.get('amount', 0)),
        data.get('date') or logic.get_today_str(),
        data.get('currency', 'TWD'),
        note=data.get('note') or None
    )
    return jsonify(result)

@app.route('/api/transfer', methods=['POST'])
def api_transfer():
    if "user_name" not in session: return jsonify({"error": "尚未登入"}), 401
    from_name = session["user_name"]
    data = request.json
    result = logic.transfer_money(
        from_name, data.get('to_name'),
        float(data.get('amount', 0)),
        data.get('date') or logic.get_today_str(),
        data.get('currency', 'TWD'),
        note=data.get('note') or None
    )
    return jsonify(result)

@app.route('/api/exchange-currency', methods=['POST'])
def api_exchange_currency():
    if "user_name" not in session: return jsonify({"error": "尚未登入"}), 401
    name = session["user_name"]
    data = request.json
    result = logic.exchange_currency(
        name, data.get('from_currency'), data.get('to_currency'),
        float(data.get('from_amount', 0)),
        data.get('date') or logic.get_today_str()
    )
    return jsonify(result)

@app.route('/api/my-transactions', methods=['GET'])
def api_get_my_transactions():
    if "user_name" not in session: return jsonify({"error": "尚未登入"}), 401
    name = session["user_name"]
    month = request.args.get('month') or None
    transactions = logic.get_my_transactions(name, month=month)
    return jsonify(transactions)

@app.route('/api/export-transactions', methods=['GET'])
def api_export_transactions():
    if "user_name" not in session: return jsonify({"error": "尚未登入"}), 401
    name = session["user_name"]
    csv_data = logic.get_my_transactions_as_csv(name)
    if csv_data is None: return jsonify({"error": "沒有交易紀錄可匯出"}), 404
    response = make_response(csv_data.encode('utf-8-sig'))
    response.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
    response.headers['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    return response

@app.route('/api/my-profile', methods=['POST'])
def api_update_my_profile():
    if "user_name" not in session: return jsonify({"error": "尚未登入"}), 401
    name = session["user_name"]
    data = request.json
    result = logic.update_my_email(name, data.get('email'))
    return jsonify(result)

@app.route('/api/change-password', methods=['POST'])
def api_change_password():
    if "user_name" not in session: return jsonify({"error": "尚未登入"}), 401
    name = session["user_name"]
    data = request.json
    result = logic.change_password(name, data.get('old_password'), data.get('new_password'))
    return jsonify(result)

@app.route('/api/exchange-rates', methods=['GET'])
def api_get_exchange_rates():
    if "user_name" not in session: return jsonify({"error": "尚未登入"}), 401
    # ... (此 API 邏輯不變) ...
    target_currencies = {
        "USD": {"name": "美國 (USD)", "flag": "us"}, "JPY": {"name": "日本 (JPY)", "flag": "jp"},
        "EUR": {"name": "歐元區 (EUR)", "flag": "eu"}, "CNY": {"name": "中國 (CNY)", "flag": "cn"},
        "HKD": {"name": "香港 (HKD)", "flag": "hk"}, "GBP": {"name": "英國 (GBP)", "flag": "gb"},
        "AUD": {"name": "澳洲 (AUD)", "flag": "au"}, "CAD": {"name": "加拿大 (CAD)", "flag": "ca"},
        "KRW": {"name": "韓國 (KRW)", "flag": "kr"}, "SGD": {"name": "新加坡 (SGD)", "flag": "sg"}
    }
    all_rates = exchange_rate.get_rates("TWD")
    if all_rates:
        filtered_rates = []
        for code, info in target_currencies.items():
            if code in all_rates:
                filtered_rates.append({
                    "code": code, "name": info["name"],
                    "flag": info["flag"], "rate": all_rates[code]
                })
        return jsonify({"success": True, "base": "TWD", "rates": filtered_rates})
    else:
        return jsonify({"success": False, "error": "無法取得匯率資料"}), 503

@app.route('/api/quote', methods=['GET'])
def api_get_quote():
    if "user_name" not in session: return jsonify({"error": "尚未登入"}), 401
    # ... (此 API 邏輯不變, 它會自動使用 logic 中的手動匯率邏輯) ...
    from_currency = request.args.get('from')
    to_currency = request.args.get('to')
    from_amount = float(request.args.get('amount', 0))
    if not all([from_currency, to_currency, from_amount > 0]):
        return jsonify({"success": False, "error": "參數不足"}), 400
    if from_currency == to_currency:
        return jsonify({"success": True, "to_amount": from_amount})
    rate = None
    manual_rates = logic.get_manual_rates()
    rate_key_direct = f"{from_currency}_{to_currency}"
    rate_key_reverse = f"{to_currency}_{from_currency}"
    if rate_key_direct in manual_rates:
        rate = manual_rates[rate_key_direct]
    elif rate_key_reverse in manual_rates and manual_rates[rate_key_reverse] > 0:
        rate = 1 / manual_rates[rate_key_reverse]
    if rate is None:
        rates = exchange_rate.get_rates(from_currency)
        if not rates: return jsonify({"success": False, "error": "無法取得匯率"}), 503
        rate = rates.get(to_currency)
        if not rate: return jsonify({"success": False, "error": f"找不到 {to_currency} 的匯率"}), 404
    to_amount = from_amount * rate
    return jsonify({"success": True, "to_amount": to_amount, "rate": rate})

# --- Analysis API (User) ---

@app.route('/api/analyze-spending', methods=['GET'])
def api_analyze_spending():
    if "user_name" not in session: return jsonify({"error": "尚未登入"}), 401
    name = session["user_name"]
    month = request.args.get('month') or None
    currency = request.args.get('currency', 'TWD') 
    result = logic.analyze_spending(name, month=month, currency=currency) 
    return jsonify(result)

@app.route('/api/analyze-income', methods=['GET'])
def api_analyze_income():
    if "user_name" not in session: return jsonify({"error": "尚未登入"}), 401
    name = session["user_name"]
    month = request.args.get('month') or None
    currency = request.args.get('currency', 'TWD') 
    result = logic.analyze_income(name, month=month, currency=currency) 
    return jsonify(result)

@app.route('/api/cash-flow-analysis', methods=['GET'])
def api_get_cash_flow_analysis():
    if "user_name" not in session: return jsonify({"error": "尚未登入"}), 401
    name = session["user_name"]
    month = request.args.get('month') or None
    currency = request.args.get('currency', 'TWD') 
    result = logic.analyze_cash_flow(name, month=month, currency=currency) 
    return jsonify(result)

# --- Budget API (User) ---

@app.route('/api/budgets', methods=['GET'])
def api_get_budgets():
    if "user_name" not in session: return jsonify({"error": "尚未登入"}), 401
    name = session["user_name"]
    month = request.args.get('month') or logic.get_this_month_str()
    currency = request.args.get('currency', 'TWD')
    result = logic.get_budgets(name, month, currency)
    return jsonify(result)

@app.route('/api/budget', methods=['POST'])
def api_set_budget():
    if "user_name" not in session: return jsonify({"error": "尚未登入"}), 401
    name = session["user_name"]
    data = request.json
    result = logic.set_budget(
        name, data.get('month') or logic.get_this_month_str(),
        data.get('currency', 'TWD'),
        data.get('category'), float(data.get('amount', 0))
    )
    return jsonify(result)

@app.route('/api/spending-vs-budget', methods=['GET'])
def api_get_spending_vs_budget():
    if "user_name" not in session: return jsonify({"error": "尚未登入"}), 401
    name = session["user_name"]
    month = request.args.get('month') or logic.get_this_month_str()
    currency = request.args.get('currency', 'TWD')
    result = logic.get_spending_vs_budget(name, month, currency)
    return jsonify(result)

# --- Web Pages ---
@app.route('/')
def index_page(): 
    if session.get("user_role") == 'admin':
        return redirect(url_for('admin_dashboard'))
    return render_template('index.html')

@app.route('/login')
def login_page(): return render_template('login.html')
@app.route('/register')
def register_page(): return render_template('register.html')

# --- Admin Web Pages ---
@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin.html')

@app.route('/admin/user/<int:user_id>')
@admin_required
def admin_user_detail(user_id):
    return render_template('admin_user_detail.html', user_id=user_id)


# --- Admin API ---
@app.route('/api/admin/stats')
@admin_required
def api_admin_stats():
    result = logic.get_system_stats()
    return jsonify(result)

@app.route('/api/admin/users')
@admin_required
def api_admin_get_users():
    users = logic.admin_get_all_users()
    return jsonify(users)

@app.route('/api/admin/user/<int:user_id>')
@admin_required
def api_admin_get_user_detail(user_id):
    # (*** (新) 修正: 此 API 不再回傳交易 ***)
    result = logic.admin_get_user_details(user_id)
    return jsonify(result)

# (*** (新) Admin API: 取得特定使用者的交易 (Req 5A) ***)
@app.route('/api/admin/user/<int:user_id>/transactions')
@admin_required
def api_admin_get_user_transactions(user_id):
    # 先取得 user_id 對應的 user_name
    conn = database.get_db_conn()
    user = conn.execute("SELECT name FROM customers WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if not user:
        return jsonify({"error": "查無此人"}), 404
        
    month = request.args.get('month') or None
    transactions = logic.get_my_transactions(user['name'], month=month)
    return jsonify(transactions)


@app.route('/api/admin/user/<int:user_id>/update', methods=['PUT'])
@admin_required
def api_admin_update_user(user_id):
    data = request.json
    result = logic.admin_update_user(
        user_id, data.get('email'), 
        data.get('role'), data.get('is_active', False)
    )
    return jsonify(result)

@app.route('/api/admin/user/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def api_admin_reset_password(user_id):
    result = logic.admin_reset_password(user_id)
    return jsonify(result)
    
@app.route('/api/admin/manual-adjustment', methods=['POST'])
@admin_required
def api_admin_manual_adjustment():
    admin_name = session["user_name"]
    data = request.json
    result = logic.admin_manual_adjustment(
        admin_name, data.get('user_id'), data.get('currency'),
        float(data.get('amount', 0)), data.get('note')
    )
    return jsonify(result)

@app.route('/api/admin/manual-rates', methods=['GET'])
@admin_required
def api_admin_get_rates():
    rates = logic.get_manual_rates()
    return jsonify({"success": True, "rates": rates})

@app.route('/api/admin/manual-rates', methods=['POST'])
@admin_required
def api_admin_set_rates():
    data = request.json
    result = logic.set_manual_rates(data.get('rates', {}))
    return jsonify(result)


# --- CLI ---
@app.cli.command('init-db')
def init_db_command(): 
    print("正在刪除舊資料庫 (如果存在)...")
    database.init_db()
    print("資料庫初始化完成。")

@app.cli.command('create-admin')
@click.argument('name')
@click.argument('password')
def create_admin_command(name, password):
    result = logic.register_customer(name, password, 0, logic.get_today_str(), role='admin')
    if result["success"]: print(f"管理員 {name} 建立成功。")
    else: print(f"建立失敗: {result['error']}")

if __name__ == '__main__':
    app.run(debug=True)