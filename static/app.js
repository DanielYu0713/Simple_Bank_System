// (新的 app.js - 整合版)
document.addEventListener('DOMContentLoaded', async () => {

    // --- 0. 全域變數 ---
    let currentUser = null;
    let myCurrencies = ['TWD']; // 預設
    
    // 圖表物件
    let cashFlowTotalChart = null;
    let cashFlowCurveChart = null;
    let cashFlowIncomeSourcesChart = null;
    let cashFlowSpendSourcesChart = null;
    let cashFlowCumulativeChart = null; 
    let budgetChart = null; // (*** (新) 預算圖表 ***)

    const ALL_CURRENCIES = ['TWD', 'USD', 'JPY', 'EUR', 'CNY', 'HKD', 'GBP', 'AUD', 'CAD', 'KRW', 'SGD'];

    // --- 1. 立即檢查登入狀態 ---
    try {
        const sessionResponse = await fetch('/api/session');
        if (!sessionResponse.ok) throw new Error('Session check failed');
        const sessionData = await sessionResponse.json();
        if (!sessionData.is_logged_in) {
            window.location.href = '/login'; return;
        }
        currentUser = sessionData;
        
        // (*** (新) 如果是 admin，顯示連結 ***)
        if (currentUser.is_admin) {
            const adminLink = document.getElementById('admin-panel-link');
            if(adminLink) adminLink.style.display = 'inline-block';
        }
    } catch (e) {
        console.error('Session check error:', e);
        window.location.href = '/login'; return;
    }

    // --- 2. 獲取所有 HTML 元素 ---
    const statusDiv = document.getElementById('status-message');
    
    // 個人資訊
    const welcomeMsg = document.getElementById('welcome-message');
    const infoName = document.getElementById('info-name');
    const infoRole = document.getElementById('info-role');
    const infoWalletsList = document.getElementById('info-wallets-list');
    const infoTotalAssets = document.getElementById('info-total-assets'); 
    
    // 管理員
    const customerListArea = document.getElementById('customer-list-area'); 
    const customerListUl = document.getElementById('customer-list');
    
    // 登出
    const btnLogout = document.getElementById('btn-logout'); 
    
    // 存款
    const btnDeposit = document.getElementById('btn-deposit');
    const depositAmount = document.getElementById('deposit-amount');
    const depositDate = document.getElementById('deposit-date');
    const depositCurrencySelect = document.getElementById('deposit-currency');

    // 提款
    const btnWithdraw = document.getElementById('btn-withdraw');
    const withdrawAmount = document.getElementById('withdraw-amount');
    const withdrawDate = document.getElementById('withdraw-date');
    const withdrawCurrencySelect = document.getElementById('withdraw-currency');
    const withdrawNote = document.getElementById('withdraw-note'); // (*** (新) ***)

    // 轉帳
    const btnTransfer = document.getElementById('btn-transfer');
    const transferToName = document.getElementById('transfer-to-name');
    const transferAmount = document.getElementById('transfer-amount');
    const transferDate = document.getElementById('transfer-date');
    const transferCurrencySelect = document.getElementById('transfer-currency');
    const transferNote = document.getElementById('transfer-note'); // (*** (新) ***)

    // 換匯 (主頁籤)
    const exchangeOpTab = document.getElementById('exchange-op-tab');
    const btnExchange = document.getElementById('btn-exchange');
    const exchangeFromCurrencySelect = document.getElementById('exchange-from-currency');
    const exchangeToCurrencySelect = document.getElementById('exchange-to-currency');
    const exchangeAmountInput = document.getElementById('exchange-amount');
    const exchangeDateInput = document.getElementById('exchange-date');
    const exchangeQuoteResult = document.getElementById('exchange-quote-result');
    
    // 右側分析小工具
    const btnAnalyzeSummary = document.getElementById('btn-analyze-summary');
    const analysisSummaryMonth = document.getElementById('analysis-summary-month');
    const analysisSummaryCurrencySelect = document.getElementById('analysis-summary-currency'); 
    const analysisSummaryLoading = document.getElementById('analysis-summary-loading');
    const analysisSummaryResults = document.getElementById('analysis-summary-results');

    // 交易紀錄
    const historyTabButton = document.getElementById('history-tab');
    const btnRefreshHistory = document.getElementById('btn-refresh-history');
    const historyTableBody = document.getElementById('history-table-body');
    const historyMonthInput = document.getElementById('history-month');
    const btnExportCsv = document.getElementById('btn-export-csv');
    
    // 外匯看板
    const exchangeTabButton = document.getElementById('exchange-tab');
    const exchangeLoading = document.getElementById('exchange-loading');
    const exchangeRateList = document.getElementById('exchange-rate-list');

    // 收支總覽
    const cashFlowTab = document.getElementById('cash-flow-tab');
    const btnAnalyzeCashFlow = document.getElementById('btn-analyze-cash-flow');
    const cashFlowMonthInput = document.getElementById('cash-flow-month');
    const cashFlowCurrencySelect = document.getElementById('cash-flow-currency'); 
    const cashFlowLoading = document.getElementById('cash-flow-loading');
    const cashFlowChartsArea = document.getElementById('cash-flow-charts-area');
    const cashFlowTotalSummary = document.getElementById('cash-flow-total-summary');
    const cashFlowSuggestion = document.getElementById('cash-flow-suggestion'); 
    const ctxCashFlowTotal = document.getElementById('cash-flow-total-chart')?.getContext('2d');
    const ctxCashFlowCurve = document.getElementById('cash-flow-curve-chart')?.getContext('2d');
    const ctxCashFlowIncomeSources = document.getElementById('cash-flow-income-sources-chart')?.getContext('2d');
    const ctxCashFlowSpendSources = document.getElementById('cash-flow-spend-sources-chart')?.getContext('2d');
    const ctxCashFlowCumulative = document.getElementById('cash-flow-cumulative-chart')?.getContext('2d'); 
    
    // (*** (新) 預算 ***)
    const budgetTab = document.getElementById('budget-tab');
    const budgetMonthInput = document.getElementById('budget-month');
    const budgetCurrencySelect = document.getElementById('budget-currency');
    const budgetLoading = document.getElementById('budget-loading');
    const budgetArea = document.getElementById('budget-area');
    const budgetSettingsList = document.getElementById('budget-settings-list');
    const btnSaveBudgets = document.getElementById('btn-save-budgets');
    const ctxBudgetChart = document.getElementById('budget-chart')?.getContext('2d');
    const budgetSummaryBars = document.getElementById('budget-summary-bars');

    // 個人設定
    const profileTabButton = document.getElementById('profile-tab');
    const profileEmailInput = document.getElementById('profile-email');
    const btnSaveProfile = document.getElementById('btn-save-profile');
    const oldPasswordInput = document.getElementById('old-password'); // (*** (新) ***)
    const newPasswordInput = document.getElementById('new-password'); // (*** (新) ***)
    const btnChangePassword = document.getElementById('btn-change-password'); // (*** (新) ***)
    
    // --- 3. 核心輔助函式 ---
    
    function showStatus(message, isError = false) {
        statusDiv.innerHTML = '';
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert ${isError ? 'alert-danger' : 'alert-success'} alert-dismissible fade show`;
        alertDiv.role = "alert";
        alertDiv.innerText = message;
        alertDiv.innerHTML += '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
        statusDiv.appendChild(alertDiv);

        if (!isError) {
            setTimeout(() => {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alertDiv);
                if (bsAlert) {
                    bsAlert.close();
                }
            }, 3000);
        }
    }

    // (*** (新) 支援 'ALL' 選項 ***)
    function populateCurrencySelect(selectElement, currencies, includeAll = false, includeAllOption = false) {
        if (!selectElement) return; 
        selectElement.innerHTML = '';
        
        if (includeAllOption) {
            const option = new Option('總資產 (TWD)', 'ALL');
            selectElement.appendChild(option);
        }
        
        const currenciesToPopulate = includeAll ? ALL_CURRENCIES : currencies;
        
        currenciesToPopulate.forEach(c => {
            const option = new Option(c, c);
            selectElement.appendChild(option);
        });
    }

    async function refreshAccountInfo() {
        try {
            const res = await fetch('/api/session');
            if (!res.ok) throw new Error('Session check failed');
            const data = await res.json();
            
            if (data.is_logged_in) {
                currentUser = data; 
                if (welcomeMsg) welcomeMsg.textContent = `歡迎, ${currentUser.user_name}`;
                if (infoName) infoName.textContent = currentUser.user_name;
                if (infoRole) infoRole.textContent = currentUser.user_role;
                if (profileEmailInput) profileEmailInput.value = currentUser.email || '';
                
                if (infoTotalAssets) infoTotalAssets.textContent = `$ ${parseFloat(currentUser.total_twd_value).toFixed(2)}`;

                infoWalletsList.innerHTML = '';
                if (currentUser.wallets && currentUser.wallets.length > 0) {
                    currentUser.wallets.forEach(wallet => {
                        const div = document.createElement('div');
                        div.className = 'd-flex justify-content-between align-items-center mb-2';
                        div.innerHTML = `
                            <div>
                                <span class="wallet-balance">${parseFloat(wallet.balance).toFixed(2)}</span>
                                <span class="wallet-currency">${wallet.currency}</span>
                            </div>
                        `;
                        infoWalletsList.appendChild(div);
                    });
                } else {
                    infoWalletsList.innerHTML = '<span class="text-muted">您目前沒有任何錢包</span>';
                }

                myCurrencies = currentUser.wallets ? currentUser.wallets.map(w => w.currency) : ['TWD'];
                
                populateCurrencySelect(depositCurrencySelect, ALL_CURRENCIES, true);
                populateCurrencySelect(withdrawCurrencySelect, myCurrencies);
                populateCurrencySelect(transferCurrencySelect, myCurrencies);
                populateCurrencySelect(exchangeFromCurrencySelect, myCurrencies);
                populateCurrencySelect(exchangeToCurrencySelect, ALL_CURRENCIES, true);

                // 填入分析下拉選單
                populateCurrencySelect(cashFlowCurrencySelect, myCurrencies, false, true); // (*** (新) 支援 'ALL' ***)
                populateCurrencySelect(analysisSummaryCurrencySelect, myCurrencies, false, true); // (*** (新) 支援 'ALL' ***)
                populateCurrencySelect(budgetCurrencySelect, myCurrencies, false, false); // (*** (新) 預算 ***)

            } else {
                window.location.href = '/login';
            }
        } catch (e) {
            showStatus(`無法載入帳戶資訊: ${e.message}`, true);
        }
    }
    
    async function refreshCustomerList() {
        if (currentUser.user_role !== 'admin') {
            if (customerListArea) customerListArea.style.display = 'none'; return;
        }
        if (customerListArea) customerListArea.style.display = 'block';
        try {
            const response = await fetch('/api/customers');
            const customers = await response.json();
            customerListUl.innerHTML = ''; 
            customers.forEach(customer => {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.textContent = `${customer.name} (${customer.role})`;
                customerListUl.appendChild(li);
            });
        } catch (error) { showStatus(`無法載入客戶列表: ${error.message}`, true); }
    }

    async function refreshHistory() {
        // (*** 不變 ***)
        try {
            const month = historyMonthInput.value;
            let apiUrl = '/api/my-transactions';
            if (month) apiUrl += `?month=${month}`;

            const response = await fetch(apiUrl);
            const transactions = await response.json();
            historyTableBody.innerHTML = '';
            
            if (transactions.length === 0) {
                historyTableBody.innerHTML = '<tr><td colspan="7" class="text-center">沒有交易紀錄</td></tr>';
            } else {
                transactions.forEach(tx => {
                    const row = document.createElement('tr');
                    const amountClass = tx.amount > 0 ? 'text-success' : 'text-danger';
                    row.innerHTML = `
                        <td>${tx.date}</td>
                        <td>${tx.type}</td>
                        <td>${tx.currency}</td>
                        <td class="${amountClass}">${parseFloat(tx.amount).toFixed(2)}</td>
                        <td>${parseFloat(tx.balance_after).toFixed(2)}</td>
                        <td>${tx.note || ''}</td>
                        <td>${tx.exchange_rate ? parseFloat(tx.exchange_rate).toFixed(4) : 'N/A'}</td>
                    `;
                    historyTableBody.appendChild(row);
                });
            }
        } catch (error) { showStatus(`無法載入交易紀錄: ${error.message}`, true); }
    }

    async function refreshExchangeRates() {
        // (*** 不變 ***)
        exchangeRateList.innerHTML = '';
        exchangeLoading.style.display = 'block';
        try {
            const response = await fetch('/api/exchange-rates');
            const result = await response.json();
            exchangeLoading.style.display = 'none';
            if (result.success) {
                result.rates.forEach(rate => {
                    const li = document.createElement('li');
                    li.className = 'list-group-item d-flex justify-content-between align-items-center';
                    li.innerHTML = `
                        <div>
                            <span class="flag-icon flag-icon-${rate.flag} me-2" style="font-size: 1.2rem;"></span>
                            <strong>${rate.name}</strong>
                        </div>
                        <span class="badge bg-primary rounded-pill fs-6">${parseFloat(rate.rate).toFixed(6)}</span>
                    `;
                    exchangeRateList.appendChild(li);
                });
            } else { throw new Error(result.error); }
        } catch (error) {
            exchangeLoading.style.display = 'none';
            showStatus(`無法載入匯率: ${error.message}`, true);
        }
    }

    // --- 4. 處理表單提交的函式 ---

    async function handleDeposit() {
        // (*** 不變 ***)
        const payload = { 
            amount: depositAmount.value, date: depositDate.value || null, currency: depositCurrencySelect.value
        };
        if (!payload.amount || parseFloat(payload.amount) <= 0) {
            showStatus("存款金額必須為 > 0 的數字", true); return;
        }
        try {
            const res = await fetch('/api/deposit', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            const result = await res.json();
            if (result.success) {
                showStatus(`存入 ${result.currency} 成功！`, false);
                await refreshAccountInfo(); 
                depositAmount.value = ''; depositDate.value = '';
            } else { showStatus(`錯誤: ${result.error}`, true); }
        } catch (e) { showStatus(`網路請求失敗: ${e.message}`, true); }
    }

    async function handleWithdraw() {
        // (*** (新) 新增 note ***)
        const payload = { 
            amount: withdrawAmount.value, 
            date: withdrawDate.value || null, 
            currency: withdrawCurrencySelect.value,
            note: withdrawNote.value || null
        };
        if (!payload.amount || parseFloat(payload.amount) <= 0) {
            showStatus("提款金額必須為 > 0 的數字", true); return;
        }
        try {
            const res = await fetch('/api/withdraw', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            const result = await res.json();
            if (result.success) {
                showStatus(`提出 ${result.currency} 成功！`, false);
                await refreshAccountInfo();
                withdrawAmount.value = ''; withdrawDate.value = ''; withdrawNote.value = '';
            } else { showStatus(`錯誤: ${result.error}`, true); }
        } catch (e) { showStatus(`網路請求失敗: ${e.message}`, true); }
    }

    async function handleTransfer() {
        // (*** (新) 新增 note ***)
        const payload = {
            to_name: transferToName.value, 
            amount: transferAmount.value,
            date: transferDate.value || null, 
            currency: transferCurrencySelect.value,
            note: transferNote.value || null
        };
        if (!payload.to_name || !payload.amount || parseFloat(payload.amount) <= 0) {
            showStatus("轉入帳號和金額 (必須 > 0) 皆為必填", true); return;
        }
        try {
            const res = await fetch('/api/transfer', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            const result = await res.json();
            if (result.success) {
                showStatus(`轉出 ${result.currency} 成功！`, false);
                await refreshAccountInfo();
                transferToName.value = ''; transferAmount.value = ''; transferDate.value = ''; transferNote.value = '';
            } else { showStatus(`錯誤: ${result.error}`, true); }
        } catch (e) { showStatus(`網路請求失敗: ${e.message}`, true); }
    }
    
    async function handleGetQuote(fromCurrency, toCurrency, fromAmount, quoteElement) {
        // (*** 不變 ***)
        if (!fromCurrency || !toCurrency || !fromAmount || fromAmount <= 0) {
            quoteElement.style.display = 'none'; return;
        }
        
        quoteElement.style.display = 'block';
        quoteElement.innerText = "計算中...";

        try {
            const response = await fetch(`/api/quote?from=${fromCurrency}&to=${toCurrency}&amount=${fromAmount}`);
            const result = await response.json();
            
            if (result.success) {
                const rateText = result.rate ? `(匯率: ${result.rate})` : '';
                quoteElement.innerText = `約可兌換: ${parseFloat(result.to_amount).toFixed(2)} ${toCurrency} ${rateText}`;
            } else {
                quoteElement.innerText = `報價失敗: ${result.error}`;
            }
        } catch (e) {
            quoteElement.innerText = `報價失敗: ${e.message}`;
        }
    }

    async function handleExchange(fromCurrency, toCurrency, fromAmount, date) {
        // (*** 不變 ***)
        const payload = {
            from_currency: fromCurrency, to_currency: toCurrency,
            from_amount: fromAmount, date: date || null
        };
        if (!payload.from_amount || parseFloat(payload.from_amount) <= 0) {
            showStatus("金額 (必須 > 0) 為必填", true); return;
        }
        if (payload.from_currency === payload.to_currency) {
            showStatus("幣別相同，無需換匯", true); return;
        }
        
        try {
            const res = await fetch('/api/exchange-currency', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            const result = await res.json();
            if (result.success) {
                showStatus(result.message, false);
                await refreshAccountInfo(); 
                await refreshHistory();
                exchangeAmountInput.value = ''; exchangeDateInput.value = '';
            } else { showStatus(`錯誤: ${result.error}`, true); }
        } catch (e) { showStatus(`網路請求失敗: ${e.message}`, true); }
    }

    async function handleSaveProfile() {
        // (*** 不變 ***)
        const email = profileEmailInput.value;
        try {
            const payload = { email: email };
            const res = await fetch('/api/my-profile', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            const result = await res.json();
            if (result.success) {
                showStatus("Email 更新成功！", false);
                currentUser.email = result.email;
            } else { showStatus(`錯誤: ${result.error}`, true); }
        } catch (e) { showStatus(`網路請求失敗: ${e.message}`, true); }
    }

    // (*** (新) 變更密碼 ***)
    async function handleChangePassword() {
        const payload = {
            old_password: oldPasswordInput.value,
            new_password: newPasswordInput.value
        };
        if (!payload.old_password || !payload.new_password) {
            showStatus("新舊密碼皆須填寫", true); return;
        }
        try {
            const res = await fetch('/api/change-password', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
            const result = await res.json();
            if (result.success) {
                showStatus(result.message, false);
                oldPasswordInput.value = '';
                newPasswordInput.value = '';
            } else { showStatus(`錯誤: ${result.error}`, true); }
        } catch (e) { showStatus(`網路請求失敗: ${e.message}`, true); }
    }

    async function handleLogout() {
        // (*** 不變 ***)
        await fetch('/api/logout', { method: 'POST' });
        showStatus("已登出，正在跳轉...", false);
        window.location.href = '/login';
    }

    async function handleExportCsv() {
        // (*** 不變 ***)
        showStatus("正在準備 CSV 檔案...", false);
        window.open('/api/export-transactions', '_blank');
    }

    // (*** 收支總覽函式 ***)
    async function handleAnalyzeCashFlow() {
        const selectedMonth = cashFlowMonthInput.value;
        const selectedCurrency = cashFlowCurrencySelect.value;
        
        if (!selectedCurrency) {
            showStatus("請先開戶 (至少擁有一個 TWD 錢包)", true);
            return;
        }

        let statusMsg = `正在分析 ${selectedCurrency} 收支...`;
        if (selectedMonth) statusMsg = `正在分析 ${selectedMonth} 的 ${selectedCurrency} 收支...`;
        showStatus(statusMsg, false);
        
        cashFlowLoading.style.display = 'block';
        cashFlowChartsArea.style.display = 'none';
        cashFlowSuggestion.style.display = 'none'; 

        let apiUrl = `/api/cash-flow-analysis?currency=${selectedCurrency}`;
        if (selectedMonth) apiUrl += `&month=${selectedMonth}`;

        try {
            const response = await fetch(apiUrl);
            const result = await response.json();
            cashFlowLoading.style.display = 'none';

            if (result.suggestion) {
                cashFlowSuggestion.innerText = result.suggestion;
                cashFlowSuggestion.style.display = 'block';
            }

            if (!result.success || Object.keys(result.summary).length === 0) {
                showStatus(selectedMonth ? `${selectedMonth} 無 ${selectedCurrency} 收支資料` : `無 ${selectedCurrency} 收支資料`, false);
                return;
            }

            cashFlowChartsArea.style.display = 'block';
            const summary = result.summary;

            // 1. 總收支 (Doughnut)
            if (cashFlowTotalChart) cashFlowTotalChart.destroy();
            cashFlowTotalChart = new Chart(ctxCashFlowTotal, {
                type: 'doughnut',
                data: {
                    labels: ['總收入', '總支出'],
                    datasets: [{
                        data: [summary.total_income, summary.total_spend],
                        backgroundColor: ['#198754', '#DC3545'] 
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
            cashFlowTotalSummary.innerHTML = `
                <span class="text-success">收入: ${summary.total_income.toFixed(2)}</span> / 
                <span class="text-danger">支出: ${summary.total_spend.toFixed(2)}</span>
            `;

            // 2. 每日流量 (Line)
            if (cashFlowCurveChart) cashFlowCurveChart.destroy();
            cashFlowCurveChart = new Chart(ctxCashFlowCurve, {
                type: 'line',
                data: {
                    labels: Object.keys(summary.daily_flow),
                    datasets: [
                        { label: '收入', data: Object.values(summary.daily_flow).map(d => d.income), borderColor: '#198754', fill: false },
                        { label: '支出', data: Object.values(summary.daily_flow).map(d => d.spend), borderColor: '#DC3545', fill: false }
                    ]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });
            
            // 3. 收入來源 (Pie)
            if (cashFlowIncomeSourcesChart) cashFlowIncomeSourcesChart.destroy();
            cashFlowIncomeSourcesChart = new Chart(ctxCashFlowIncomeSources, {
                type: 'pie',
                data: {
                    labels: Object.keys(summary.income_sources),
                    datasets: [{ data: Object.values(summary.income_sources), backgroundColor: ['#198754', '#20c997', '#0dcaf0', '#6f42c1'] }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });

            // 4. 支出來源 (Pie)
            if (cashFlowSpendSourcesChart) cashFlowSpendSourcesChart.destroy();
            cashFlowSpendSourcesChart = new Chart(ctxCashFlowSpendSources, {
                type: 'pie',
                data: {
                    labels: Object.keys(summary.spend_sources),
                    datasets: [{ data: Object.values(summary.spend_sources), 
                        backgroundColor: ['#DC3545', '#fd7e14', '#ffc107', '#d63384', '#6610f2', '#0d6efd', '#adb5bd'] 
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false }
            });

            // 5. 累積流量
            if (summary.cumulative_flow) {
                if (cashFlowCumulativeChart) cashFlowCumulativeChart.destroy();
                cashFlowCumulativeChart = new Chart(ctxCashFlowCumulative, {
                    type: 'line',
                    data: {
                        labels: Object.keys(summary.cumulative_flow),
                        datasets: [
                            { label: '累計收入', data: Object.values(summary.cumulative_flow).map(d => d.income), borderColor: '#198754', fill: false, tension: 0.1 },
                            { label: '累計支出', data: Object.values(summary.cumulative_flow).map(d => d.spend), borderColor: '#DC3545', fill: false, tension: 0.1 }
                        ]
                    },
                    options: { responsive: true, maintainAspectRatio: false }
                });
            }


        } catch (error) {
            cashFlowLoading.style.display = 'none';
            showStatus(`分析失敗: ${error.message}`, true);
        }
    }

    // (*** 右側分析小工具函式 ***)
    async function handleAnalyzeSummary() {
        const month = analysisSummaryMonth.value;
        const selectedCurrency = analysisSummaryCurrencySelect.value;
        
        if (!selectedCurrency) {
             analysisSummaryResults.innerHTML = `<p class="text-muted small">請先開戶 (至少擁有一個 TWD 錢包)</p>`;
            return;
        }

        analysisSummaryLoading.style.display = 'block';
        analysisSummaryResults.innerHTML = '';
        
        let spendUrl = `/api/analyze-spending?currency=${selectedCurrency}`;
        let incomeUrl = `/api/analyze-income?currency=${selectedCurrency}`;
        if (month) {
            spendUrl += `&month=${month}`;
            incomeUrl += `&month=${month}`;
        }
        
        try {
            const [spendResponse, incomeResponse] = await Promise.all([
                fetch(spendUrl),
                fetch(incomeUrl)
            ]);
            
            const spendData = await spendResponse.json();
            const incomeData = await incomeResponse.json();
            
            analysisSummaryLoading.style.display = 'none';
            
            let html = '';
            
            // 處理收入
            html += `<h6 class="text-success">${selectedCurrency} 收入分析 (次數)</h6>`;
            if (incomeData.success && Object.keys(incomeData.summary).length > 0) {
                html += '<ul class="list-group list-group-flush mb-3">';
                for (const [key, value] of Object.entries(incomeData.summary)) {
                    html += `<li class="list-group-item d-flex justify-content-between align-items-center p-1">
                                ${key}: <span class="badge bg-success rounded-pill">${value} 次</span>
                             </li>`;
                }
                html += '</ul>';
            } else {
                html += `<p class="text-muted small">${incomeData.message || '無收入資料'}</p>`;
            }
            
            // 處理支出
            html += `<h6 class="text-danger">${selectedCurrency} 支出分析 (次數)</h6>`;
            if (spendData.success && Object.keys(spendData.summary).length > 0) {
                html += '<ul class="list-group list-group-flush mb-3">';
                for (const [key, value] of Object.entries(spendData.summary)) {
                    html += `<li class="list-group-item d-flex justify-content-between align-items-center p-1">
                                ${key}: <span class="badge bg-danger rounded-pill">${value} 次</span>
                             </li>`;
                }
                html += '</ul>';
                if (spendData.suggestion) {
                    html += `<div class="alert alert-warning small p-2 mt-2">${spendData.suggestion}</div>`;
                }
            } else {
                html += `<p class="text-muted small">${spendData.message || '無支出資料'}</p>`;
            }
            
            analysisSummaryResults.innerHTML = html;

        } catch (e) {
            analysisSummaryLoading.style.display = 'none';
            analysisSummaryResults.innerHTML = `<p class="text-danger">分析載入失敗: ${e.message}</p>`;
        }
    }
    
    // (*** (新) 預算函式 ***)
    async function handleLoadBudgets() {
        const month = budgetMonthInput.value || new Date().toISOString().slice(0, 7);
        budgetMonthInput.value = month;
        const currency = budgetCurrencySelect.value;
        
        if (!currency) return;
        
        budgetLoading.style.display = 'block';
        budgetArea.style.display = 'none';
        
        try {
            const [budgetRes, vsRes] = await Promise.all([
                fetch(`/api/budgets?month=${month}&currency=${currency}`),
                fetch(`/api/spending-vs-budget?month=${month}&currency=${currency}`)
            ]);
            
            const budgetData = await budgetRes.json();
            const vsData = await vsRes.json();
            
            budgetLoading.style.display = 'none';
            budgetArea.style.display = 'block';

            // 1. 填入預算設定
            budgetSettingsList.innerHTML = '';
            if (budgetData.success) {
                budgetData.categories.forEach(category => {
                    const amount = budgetData.budgets[category] || 0;
                    budgetSettingsList.innerHTML += `
                        <div class="input-group mb-2">
                            <span class="input-group-text" style="width: 120px;">${category}</span>
                            <input type="number" class="form-control budget-input" 
                                   data-category="${category}" value="${amount}" min="0">
                        </div>
                    `;
                });
            }
            
            // 2. 繪製圖表和進度條
            budgetSummaryBars.innerHTML = '';
            if (vsData.success) {
                const labels = vsData.comparison.map(c => c.category);
                const budgetValues = vsData.comparison.map(c => c.budget);
                const spentValues = vsData.comparison.map(c => c.spent);
                
                if (budgetChart) budgetChart.destroy();
                budgetChart = new Chart(ctxBudgetChart, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            { label: '預算', data: budgetValues, backgroundColor: 'rgba(54, 162, 235, 0.5)' },
                            { label: '已支出', data: spentValues, backgroundColor: 'rgba(255, 99, 132, 0.5)' }
                        ]
                    },
                    options: { indexAxis: 'y', responsive: true, scales: { x: { stacked: false }, y: { stacked: false } } }
                });
                
                // 3. 繪製進度條
                vsData.comparison.forEach(c => {
                    if (c.budget > 0 || c.spent > 0) {
                        const percent = c.budget > 0 ? (c.spent / c.budget) * 100 : 100;
                        const isOver = c.spent > c.budget;
                        budgetSummaryBars.innerHTML += `
                            <div class="mb-2">
                                <div class="d-flex justify-content-between small">
                                    <span>${c.category}</span>
                                    <span class="${isOver ? 'text-danger fw-bold' : ''}">
                                        $${c.spent.toFixed(0)} / $${c.budget.toFixed(0)}
                                    </span>
                                </div>
                                <div class="budget-bar-container">
                                    <div class="budget-bar ${isOver ? 'over-budget' : ''}" 
                                         style="width: ${Math.min(percent, 100)}%;">
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                });
            }
            
        } catch (e) {
            budgetLoading.style.display = 'none';
            showStatus(`載入預算失敗: ${e.message}`, true);
        }
    }
    
    // (*** (新) 儲存預算 ***)
    async function handleSaveBudgets() {
        const month = budgetMonthInput.value;
        const currency = budgetCurrencySelect.value;
        const inputs = document.querySelectorAll('.budget-input');
        
        let hasError = false;
        
        const requests = Array.from(inputs).map(input => {
            const payload = {
                month: month,
                currency: currency,
                category: input.dataset.category,
                amount: parseFloat(input.value) || 0
            };
            return fetch('/api/budget', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        });
        
        try {
            const responses = await Promise.all(requests);
            for(const res of responses) {
                if (!res.ok) hasError = true;
            }
            if (hasError) throw new Error('部分預算儲存失敗');
            showStatus('預算儲存成功!', false);
            await handleLoadBudgets(); // 重新載入
        } catch (e) {
            showStatus(`儲存預算失敗: ${e.message}`, true);
        }
    }


    // --- 5. 綁定按鈕事件 ---
    btnDeposit.addEventListener('click', handleDeposit);
    btnWithdraw.addEventListener('click', handleWithdraw);
    btnTransfer.addEventListener('click', handleTransfer);
    btnLogout.addEventListener('click', handleLogout);
    btnExportCsv.addEventListener('click', handleExportCsv);
    btnSaveProfile.addEventListener('click', handleSaveProfile);
    btnChangePassword.addEventListener('click', handleChangePassword); // (*** (新) ***)
    
    // 換匯
    btnExchange.addEventListener('click', () => {
        handleExchange(
            exchangeFromCurrencySelect.value,
            exchangeToCurrencySelect.value,
            exchangeAmountInput.value,
            exchangeDateInput.value
        );
    });
    exchangeFromCurrencySelect.addEventListener('change', () => handleGetQuote(exchangeFromCurrencySelect.value, exchangeToCurrencySelect.value, exchangeAmountInput.value, exchangeQuoteResult));
    exchangeToCurrencySelect.addEventListener('change', () => handleGetQuote(exchangeFromCurrencySelect.value, exchangeToCurrencySelect.value, exchangeAmountInput.value, exchangeQuoteResult));
    exchangeAmountInput.addEventListener('input', () => handleGetQuote(exchangeFromCurrencySelect.value, exchangeToCurrencySelect.value, exchangeAmountInput.value, exchangeQuoteResult));

    // 右側分析
    btnAnalyzeSummary.addEventListener('click', handleAnalyzeSummary);
    analysisSummaryMonth.addEventListener('change', handleAnalyzeSummary);
    analysisSummaryCurrencySelect.addEventListener('change', handleAnalyzeSummary); 

    // 收支總覽
    btnAnalyzeCashFlow.addEventListener('click', handleAnalyzeCashFlow);
    cashFlowCurrencySelect.addEventListener('change', handleAnalyzeCashFlow); 
    cashFlowMonthInput.addEventListener('change', handleAnalyzeCashFlow); 

    // Tab 顯示時觸發的事件
    historyTabButton.addEventListener('shown.bs.tab', refreshHistory);
    profileTabButton.addEventListener('shown.bs.tab', refreshAccountInfo);
    exchangeTabButton.addEventListener('shown.bs.tab', refreshExchangeRates);
    exchangeOpTab.addEventListener('shown.bs.tab', refreshAccountInfo); 
    cashFlowTab.addEventListener('shown.bs.tab', handleAnalyzeCashFlow); 
    
    // (*** (新) 預算 ***)
    budgetTab.addEventListener('shown.bs.tab', handleLoadBudgets);
    budgetMonthInput.addEventListener('change', handleLoadBudgets);
    budgetCurrencySelect.addEventListener('change', handleLoadBudgets);
    btnSaveBudgets.addEventListener('click', handleSaveBudgets);
    
    historyMonthInput.addEventListener('change', refreshHistory);


    // --- 6. 頁面首次載入 ---
    await refreshAccountInfo(); 
    refreshCustomerList();
    handleAnalyzeSummary(); 
});