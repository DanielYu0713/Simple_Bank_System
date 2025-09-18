# (新檔案: exchange_rate.py)
#用來處理呼叫外部 API 的邏輯。我們還會加入「快取」(Cache) 機制，避免每次刷新都去呼叫 API（免費版有請求限制）
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv() # 確保環境變數被載入

API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")
BASE_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/"

# 簡單的記憶體快取 (cache)，避免過度請求 API
# 格式: { "貨幣": (時間戳, 匯率資料) }
_cache = {}
CACHE_DURATION_SECONDS = 3600 # 快取 1 小時 (3600 秒)

def get_rates(base_currency="TWD"):
    """
    取得指定貨幣的匯率，並使用快取
    """
    global _cache
    current_time = time.time()
    
    # 1. 檢查快取是否有效
    if base_currency in _cache:
        cache_time, cache_data = _cache[base_currency]
        if current_time - cache_time < CACHE_DURATION_SECONDS:
            print("[Cache] Using cached exchange rates.")
            return cache_data

    # 2. 快取失效或不存在，呼叫 API
    if not API_KEY:
        print("錯誤: 尚未設定 EXCHANGE_RATE_API_KEY")
        return None

    try:
        print("[API] Fetching new exchange rates...")
        response = requests.get(f"{BASE_URL}{base_currency}")
        response.raise_for_status() # 檢查 HTTP 錯誤
        data = response.json()
        
        if data.get("result") == "success":
            rates = data.get("conversion_rates")
            # 3. 更新快取
            _cache[base_currency] = (current_time, rates)
            return rates
        else:
            print(f"匯率 API 錯誤: {data.get('error-type')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"匯率 API 呼叫失敗: {e}")
        return None