# (新檔案: email_service.py)
import smtplib
import os
from email.message import EmailMessage

# --- 從 .env 讀取 SMTP 設定 ---
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT", 587) # 587 (TLS) 或 465 (SSL)
SMTP_USER = os.getenv("SMTP_USER") # 您的 Email
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD") # 您的 Email 密碼或應用程式密碼

def send_email(to_address, subject, body):
    """
    寄送一封純文字 Email。
    
    警告: 您必須在 .env 檔案中設定 SMTP 相關變數!
    """
    if not all([SMTP_SERVER, SMTP_USER, SMTP_PASSWORD]):
        print(f"Email 服務未設定: 無法寄送 Email 給 {to_address}")
        return False
        
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = to_address
    
    try:
        print(f"正在嘗試寄送 Email 至 {to_address}...")
        if int(SMTP_PORT) == 465:
            # 使用 SSL
            with smtplib.SMTP_SSL(SMTP_SERVER, int(SMTP_PORT)) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            # 使用 TLS
            with smtplib.SMTP(SMTP_SERVER, int(SMTP_PORT)) as server:
                server.starttls() # 啟用 TLS
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
        
        print(f"Email 寄送成功: {subject}")
        return True
    except Exception as e:
        print(f"Email 寄送失敗: {e}")
        return False

# --- 範本 ---
def send_transfer_notification(to_address, from_name, amount, currency, to_name):
    subject = "[銀行系統] 轉帳通知"
    body = f"""
    您好,
    
    {from_name} 剛剛轉出了一筆款項:
    
    金額: {amount:,.2f} {currency}
    轉給: {to_name}
    
    這是一封自動通知信。
    """
    send_email(to_address, subject, body)

def send_exchange_notification(to_address, from_amount, from_currency, to_amount, to_currency):
    subject = "[銀行系統] 換匯通知"
    body = f"""
    您好,
    
    您剛剛完成了一筆換匯交易:
    
    轉出: {from_amount:,.2f} {from_currency}
    換得: {to_amount:,.2f} {to_currency}
    
    這是一封自動通知信。
    """
    send_email(to_address, subject, body)

def send_password_reset_notification(to_address, new_password):
    subject = "[銀行系統] 密碼重設通知"
    body = f"""
    您好,
    
    管理員已為您重設密碼。您的新密碼是:
    
    {new_password}
    
    請立即登入並變更您的密碼。
    """
    send_email(to_address, subject, body)