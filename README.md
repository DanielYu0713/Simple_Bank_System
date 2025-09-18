# 簡易銀行系統 (Simple Bank System)

這是一個使用 Flask 和 SQLite 打造的網頁版簡易銀行系統，具備多幣別錢包、轉帳、AI 智慧消費分析與收入分析等核心功能。

## 系統截圖 (System Screenshots)

*儀表板主畫面*
![儀表板](static/img/使用者功能介面.png)

*財務分析圖表*
![分析圖表](static/img/財務分析.png)

## 功能特色 (Features)

- **使用者系統**: 支援註冊、登入、登出。
- **管理員後台**: 可查看所有客戶列表。
- **多幣別錢包**: 支援 TWD, USD, JPY 等多種貨幣，可分別存提款。
- **銀行交易**: 
    - **存款**: 存入指定幣別至錢包。
    - **提款**: 從指定幣別錢包提款。
    - **轉帳**: 在使用者之間進行同幣別轉帳。
    - **換匯**: 根據即時匯率進行不同幣別之間的兌換。
- **智慧分析**: 
    - **消費分析**: 使用 AI 將支出備註自動分類 (如：餐飲、交通)，並將提款、轉帳、換匯等資產轉移獨立計算，以圓餅圖呈現各類別支出**次數**。
    - **收入分析**: 將存款、轉入、換匯等收入來源進行分類，以甜甜圈圖呈現各類別收入**次數**。
- **交易紀錄**: 查看所有交易的詳細歷史，並可依月份篩選。
- **CSV 匯出**: 將交易紀錄匯出為 CSV 檔案。

## 技術棧 (Tech Stack)

- **後端**: Python, Flask
- **資料庫**: SQLite
- **前端**: JavaScript, Bootstrap 5, Chart.js
- **AI 服務**: `ai_services.py` (可串接外部如 Gemini 等大型語言模型)
- **匯率服務**: `exchange_rate.py` (串接外部匯率 API)

## 專案結構 (Project Structure)

```
.
├── templates/         # HTML 網頁模板
│   ├── index.html       # 主儀表板
│   ├── login.html       # 登入頁面
│   └── ...
├── static/              # 靜態檔案 (JS, CSS, 圖片)
│   ├── js/              # JavaScript 檔案
│   └── img/             # 圖片資源
├── .env                 # 環境變數檔案 (範本)
├── app.py               # Flask 主應用程式，定義所有路由 (Routes)
├── logic.py             # 核心商業邏輯 (使用者、交易、分析等)
├── database.py          # 資料庫連線與初始化
├── schema.sql           # 資料庫結構 (DDL)
├── ai_services.py       # AI 分類服務
├── exchange_rate.py     # 匯率 API 服務
├── requirements.txt     # Python 依賴套件
└── README.md            # 本說明檔案
```

## 安裝與啟動 (Installation & Setup)

1.  **前置準備**: 請確保您的電腦已安裝 Python 3。

2.  **建立虛擬環境**:
    ```bash
    # 建立一個名為 venv 的虛擬環境
    python -m venv venv
    ```

3.  **啟動虛擬環境**:
    -   Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    -   macOS / Linux:
        ```bash
        source venv/bin/activate
        ```

4.  **安裝依賴套件**:
    (若專案中沒有 `requirements.txt`，請先手動安裝)
    ```bash
    pip install Flask Flask-Session python-dotenv werkzeug
    ```
    建議建立 `requirements.txt` 檔案以便他人快速安裝：
    ```bash
    pip freeze > requirements.txt
    ```

5.  **初始化資料庫**:
    ```bash
    # 設定 Flask App 環境變數
    # Windows
    set FLASK_APP=app.py
    # macOS / Linux
    export FLASK_APP=app.py

    # 執行資料庫初始化指令
    flask init-db
    ```

6.  **建立管理員帳號**:
    ```bash
    # flask create-admin <管理員名稱> <管理員密碼>
    flask create-admin admin admin123
    ```

7.  **啟動應用程式**:
    ```bash
    flask run
    ```
    啟動後，在瀏覽器開啟 `http://127.0.0.1:5000` 即可看到登入頁面。

## 未來可改進部分 (Future Improvements)

- **分析功能增強**: 
    - 除了分析「次數」，也可以改為分析「金額」。
    - 支援 TWD 以外的其他幣別分析。
- **使用者體驗 (UX)**: 
    - 使用 AJAX 或 WebSocket 技術，讓錢包餘額在交易後可以局部更新，無需重新整理頁面。
    - 圖表可以做得更具互動性，例如點擊圖表區塊後顯示該分類的詳細交易。
- **測試**: 
    - 補全單元測試 (Unit Tests) 和整合測試 (Integration Tests)，確保程式碼品質。
- **安全性強化**: 
    - 增加更嚴格的密碼策略。
    - 針對所有使用者輸入進行更嚴謹的驗證與清理，防止 XSS 攻擊。
    - 啟用 Flask 的 CSRF 保護機制。
- **非同步任務**: 
    - 對於呼叫 AI 服務等可能耗時較長的任務，可以改用 Celery 或 RQ 等非同步任務佇列來處理，避免網頁請求被卡住。
