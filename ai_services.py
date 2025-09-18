import requests
import os

# 1. 讀取我們存在環境變數中的 Token
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
print(f"[除錯] 載入的 Hugging Face Token: {HF_API_TOKEN}") # <-- 新增這行

# 2. 選擇一個 Zero-Shot 分類模型 (更換成另一個模型進行測試)
MODEL_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"

# 3. 準備 API 呼叫的標頭
headers = {
    "Authorization": f"Bearer {HF_API_TOKEN}"
}

def categorize_spending(notes_list, categories):
    """
    使用 Hugging Face API 將一組交易備註分類
    :param notes_list: [ "7-11 購物", "計程車費", "看電影" ]
    :param categories: [ "餐飲美食", "交通出行", "休閒娛樂", "其他" ]
    :return: AI 的原始回覆，或在失敗時回傳 None
    """
    if not notes_list:
        return None
        
    payload = {
        "inputs": notes_list,
        "parameters": {
            "candidate_labels": categories
        }
    }
    
    try:
        response = requests.post(MODEL_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status() # 如果 API 回傳 4xx or 5xx 錯誤，就拋出異常
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"AI API 呼叫失敗: {e}")
        # 在真實應用中，這裡可能需要處理速率限制 (rate limits) 的問題
        return None