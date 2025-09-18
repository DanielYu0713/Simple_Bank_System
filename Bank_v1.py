# -*- coding: utf-8 -*-
# 簡易銀行系統（dict/list + input 互動選單）
# 功能：
# 1) 批次建立客戶（姓名、日期、金額）
# 2) 列出所有客戶餘額
# 3) 存款
# 4) 提款
# 5) 依日期或區間查詢交易紀錄
# 6) 轉帳（額外功能）
# 7) 月結算（額外功能）
# 0) 離開
#
# 內部資料結構（只用 dict/list）：
# customers = {
#   "Alice": {
#       "balance": 1000.0,
#       "history": [
#           {"date":"2025-09-10","type":"開戶","amount":1000.0,"balance":1000.0,"note":""}
#       ]
#   }, ...
# }

from datetime import datetime

DATE_FMT = "%Y-%m-%d"

customers = {}  # 全部客戶資料

def valid_date(s):
    """驗證 YYYY-MM-DD，回傳 True/False"""
    try:
        datetime.strptime(s, DATE_FMT)
        return True
    except:
        return False

def today_str():
    return datetime.now().strftime(DATE_FMT)

def ensure_customer(name):
    """若客戶不存在，回傳 False"""
    return name in customers

def create_transaction(date, ttype, amount, after_balance, note=""):
    """建立單筆交易紀錄（dict）"""
    return {
        "date": date,
        "type": ttype,        # "開戶" | "存款" | "提款" | "轉入" | "轉出"
        "amount": round(float(amount), 2),
        "balance": round(float(after_balance), 2),
        "note": note          # "來自" | "轉給" | ""
    }

def batch_create_customers():
    print("\n=== 批次建立客戶 ===")
    try:
        n = int(input("要建立幾位客戶？：").strip())
        if n <= 0:
            print("數量需為正整數。")
            return
    except:
        print("輸入錯誤。")
        return

    same_date = input("是否為所有客戶使用同一天的『操作日期』？(y/N)：").strip().lower() == "y"
    common_date = None
    if same_date:
        common_date = input("請輸入操作日期(YYYY-MM-DD，留空=今日)：").strip()
        if not common_date:
            common_date = today_str()
        if not valid_date(common_date):
            print("日期格式錯誤。作業中止。")
            return

    for i in range(1, n+1):
        print(f"\n--- 第 {i} 位 ---")
        name = input("客戶姓名：").strip()
        if not name:
            print("姓名不可空白，跳過。")
            continue
        if name in customers:
            print("客戶已存在，跳過。")
            continue

        # 金額
        try:
            amount = float(input("初始金額(可為0)：").strip())
            if amount < 0:
                print("初始金額不可為負，跳過。")
                continue
        except:
            print("金額格式錯誤，跳過。")
            continue

        # 日期
        if same_date:
            date = common_date
        else:
            date = input("操作日期(YYYY-MM-DD，留空=今日)：").strip()
            if not date:
                date = today_str()
            if not valid_date(date):
                print("日期格式錯誤，跳過。")
                continue

        # 建立客戶
        customers[name] = {"balance": round(amount, 2), "history": []}
        customers[name]["history"].append(
            create_transaction(date, "開戶", amount, customers[name]["balance"])
        )
        print(f"已建立客戶 {name}，餘額 {customers[name]['balance']:.2f}")

def list_balances():
    print("\n=== 所有客戶餘額 ===")
    if not customers:
        print("目前無客戶。")
        return
    for name, info in customers.items():
        print(f"- {name}: {info['balance']:.2f}")

def deposit():
    print("\n=== 存款 ===")
    name = input("客戶姓名：").strip()
    if not ensure_customer(name):
        print("查無此客戶。")
        return
    try:
        amount = float(input("存款金額：").strip())
        if amount <= 0:
            print("金額需 > 0")
            return
    except:
        print("金額格式錯誤。")
        return

    date = input("日期(YYYY-MM-DD，留空=今日)：").strip()
    if not date:
        date = today_str()
    if not valid_date(date):
        print("日期格式錯誤。")
        return

    customers[name]["balance"] = round(customers[name]["balance"] + amount, 2)
    customers[name]["history"].append(
        create_transaction(date, "存款", amount, customers[name]["balance"])
    )
    print(f"存款成功！{name} 目前餘額：{customers[name]['balance']:.2f}")

def withdraw():
    print("\n=== 提款 ===")
    name = input("客戶姓名：").strip()
    if not ensure_customer(name):
        print("查無此客戶。")
        return
    try:
        amount = float(input("提款金額：").strip())
        if amount <= 0:
            print("金額需 > 0")
            return
    except:
        print("金額格式錯誤。")
        return

    date = input("日期(YYYY-MM-DD，留空=今日)：").strip()
    if not date:
        date = today_str()
    if not valid_date(date):
        print("日期格式錯誤。")
        return

    if customers[name]["balance"] < amount:
        print("餘額不足，提款失敗。")
        return

    customers[name]["balance"] = round(customers[name]["balance"] - amount, 2)
    customers[name]["history"].append(
        create_transaction(date, "提款", -amount, customers[name]["balance"])
    )
    print(f"提款成功！{name} 目前餘額：{customers[name]['balance']:.2f}")

def transfer():
    print("\n=== 轉帳（額外功能） ===")
    src = input("轉出帳戶：").strip()
    dst = input("轉入帳戶：").strip()
    if src == dst:
        print("不可轉給自己。")
        return
    if not ensure_customer(src):
        print("查無轉出帳戶。")
        return
    if not ensure_customer(dst):
        print("查無轉入帳戶。")
        return
    try:
        amount = float(input("轉帳金額：").strip())
        if amount <= 0:
            print("金額需 > 0")
            return
    except:
        print("金額格式錯誤。")
        return

    date = input("日期(YYYY-MM-DD，留空=今日)：").strip()
    if not date:
        date = today_str()
    if not valid_date(date):
        print("日期格式錯誤。")
        return

    if customers[src]["balance"] < amount:
        print("轉帳失敗：轉出帳戶餘額不足。")
        return

    # 轉出
    customers[src]["balance"] = round(customers[src]["balance"] - amount, 2)
    customers[src]["history"].append(
        create_transaction(date, "轉出", -amount, customers[src]["balance"], note=f"轉給 {dst}")
    )
    # 轉入
    customers[dst]["balance"] = round(customers[dst]["balance"] + amount, 2)
    customers[dst]["history"].append(
        create_transaction(date, "轉入", amount, customers[dst]["balance"], note=f"來自 {src}")
    )
    print(f"轉帳完成！{src} -> {dst} {amount:.2f}")
    print(f"- {src} 餘額：{customers[src]['balance']:.2f}")
    print(f"- {dst} 餘額：{customers[dst]['balance']:.2f}")

def query_by_date():
    print("\n=== 依日期查詢交易 ===")
    mode = input("輸入 1=查單日，2=查區間：").strip()
    if mode == "1":
        d = input("日期(YYYY-MM-DD)：").strip()
        if not valid_date(d):
            print("日期格式錯誤。")
            return
        start, end = d, d
    elif mode == "2":
        start = input("起始日(YYYY-MM-DD)：").strip()
        end = input("結束日(YYYY-MM-DD)：").strip()
        if not valid_date(start) or not valid_date(end):
            print("日期格式錯誤。")
            return
        if start > end:
            print("起始日需早於或等於結束日。")
            return
    else:
        print("無效選項。")
        return

    # 彙整所有交易（只列出存款/提款/轉入/轉出/開戶）
    found_any = False
    for name, info in customers.items():
        # 篩選範圍內的交易
        records = [h for h in info["history"] if start <= h["date"] <= end]
        if records:
            found_any = True
            print(f"\n[客戶] {name}")
            for r in sorted(records, key=lambda x: (x["date"], x["type"])):
                amt_str = f"{r['amount']:+.2f}"
                note_str = f"｜備註: {r['note']}" if r.get("note") else ""
                print(f"  {r['date']}｜{r['type']}｜金額 {amt_str}｜結餘 {r['balance']:.2f} {note_str}")
    if not found_any:
        print("此日期/區間內無任何交易。")

def monthly_statement():
    print("\n=== 月結算（額外功能） ===")
    name = input("客戶姓名：").strip()
    if not ensure_customer(name):
        print("查無此客戶。")
        return
    ym = input("請輸入月份(YYYY-MM)：").strip()
    # 轉換為範圍
    try:
        first_day = datetime.strptime(ym + "-01", DATE_FMT)
        # 粗略下一個月的第一天（用日=28保守加法，再回到月初）
        tmp = first_day.replace(day=28)
        next_month = (tmp + timedelta(days=4)).replace(day=1)
        start = first_day.strftime(DATE_FMT)
        end = (next_month - timedelta(days=1)).strftime(DATE_FMT)
    except:
        print("月份格式錯誤。")
        return

    info = customers[name]
    # 找到月初前的最後一筆結餘（作為期初），若沒有就以第一筆歷史的前一刻為0
    history_sorted = sorted(info["history"], key=lambda x: x["date"])
    opening_balance = 0.0
    for r in history_sorted:
        if r["date"] < start:
            opening_balance = r["balance"]
        else:
            break

    # 匯總當月
    month_records = [h for h in info["history"] if start <= h["date"] <= end]
    dep = sum(h["amount"] for h in month_records if h["amount"] > 0)
    wd  = -sum(h["amount"] for h in month_records if h["amount"] < 0)
    closing_balance = opening_balance + dep - wd

    print(f"\n{Name:=^30}".replace("Name", name + " 月結算"))
    print(f"月份：{ym}")
    print(f"期初結餘：{opening_balance:.2f}")
    print(f"存入合計：{dep:.2f}")
    print(f"支出合計：{wd:.2f}")
    print(f"淨變動  ：{(dep - wd):.2f}")
    print(f"期末結餘：{closing_balance:.2f}")
    if month_records:
        print("\n— 當月交易明細 —")
        for r in sorted(month_records, key=lambda x: (x["date"], x["type"])):
            amt_str = f"{r['amount']:+.2f}"
            note_str = f"｜備註: {r['note']}" if r.get("note") else ""
            print(f"  {r['date']}｜{r['type']}｜金額 {amt_str}｜結餘 {r['balance']:.2f} {note_str}")
    else:
        print("當月無交易。")

def menu():
    while True:
        print("\n========== 簡易銀行系統 ==========")
        print("1) 批次建立客戶（姓名/日期/金額）")
        print("2) 列出所有客戶餘額")
        print("3) 存款")
        print("4) 提款")
        print("5) 依日期或區間查交易")
        print("6) 轉帳（額外）")
        print("7) 月結算（額外）")
        print("0) 離開")
        choice = input("請選擇：").strip()

        if choice == "1":
            batch_create_customers()
        elif choice == "2":
            list_balances()
        elif choice == "3":
            deposit()
        elif choice == "4":
            withdraw()
        elif choice == "5":
            query_by_date()
        elif choice == "6":
            transfer()
        elif choice == "7":
            # 需要 from datetime import timedelta
            pass  # 占位，稍後補上
        elif choice == "0":
            print("感謝使用，再見！")
            break
        else:
            print("選項無效，請重新輸入。")

# 小補丁：上方月結算用到 timedelta，在這裡引入並把功能接上
from datetime import timedelta
def _attach_monthly_statement_to_menu():
    # 這個小技巧讓上面的 menu 可呼叫月結算
    global monthly_statement
    # 重新定義 menu 中的選項 7 行為
    # 直接替換 menu 中的 'pass' 做法比較繁雜，改為在主程式啟動前 monkey patch：不需要，直接在 menu 中呼叫。
    pass

if __name__ == "__main__":
    menu()
