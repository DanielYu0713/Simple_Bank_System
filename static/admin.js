// (更新的: static/admin.js)
document.addEventListener('DOMContentLoaded', () => {

    const statusDiv = document.getElementById('admin-status-message');
    const btnLogout = document.getElementById('btn-admin-logout');

    // --- 輔助函式 ---
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
                if (bsAlert) bsAlert.close();
            }, 3000);
        }
    }
    
    // 登出
    if (btnLogout) {
        btnLogout.addEventListener('click', async () => {
            await fetch('/api/logout', { method: 'POST' });
            window.location.href = '/login';
        });
    }

    // 檢查登入狀態並顯示歡迎
    (async () => {
        try {
            const res = await fetch('/api/session');
            const data = await res.json();
            if (!data.is_logged_in || data.user_role !== 'admin') {
                window.location.href = '/login';
            }
            const welcome = document.getElementById('admin-welcome');
            if(welcome) welcome.textContent = `歡迎, ${data.user_name} (管理員)`;
        } catch (e) {
            window.location.href = '/login';
        }
    })();


    // --- 主儀表板 (admin.html) ---
    if (document.getElementById('users-table-body')) {
        
        const statsTotalUsers = document.getElementById('stats-total-users');
        const statsActiveUsers = document.getElementById('stats-active-users');
        const statsTotalAssets = document.getElementById('stats-total-assets');
        const assetsByCurrencyList = document.getElementById('stats-assets-by-currency'); // (*** (新) ***)
        const usersTableBody = document.getElementById('users-table-body');
        
        // 載入統計
        const loadStats = async () => {
            try {
                const res = await fetch('/api/admin/stats');
                const data = await res.json();
                if (data.success) {
                    statsTotalUsers.textContent = data.stats.total_users;
                    statsActiveUsers.textContent = data.stats.active_users;
                    statsTotalAssets.textContent = `$ ${data.stats.total_assets_twd.toFixed(2)} TWD`;

                    // (*** (新) 載入各幣別資產 (Req 5B) ***)
                    assetsByCurrencyList.innerHTML = '';
                    if (data.stats.assets_by_currency) {
                        for (const [currency, total] of Object.entries(data.stats.assets_by_currency)) {
                             const li = document.createElement('li');
                             li.className = 'list-group-item d-flex justify-content-between';
                             li.innerHTML = `${currency}: <strong>${total.toFixed(2)}</strong>`;
                             assetsByCurrencyList.appendChild(li);
                        }
                    }
                }
            } catch (e) { showStatus(`無法載入統計: ${e.message}`, true); }
        };

        // 載入使用者
        const loadUsers = async () => {
            try {
                const res = await fetch('/api/admin/users');
                const users = await res.json();
                usersTableBody.innerHTML = '';
                users.forEach(user => {
                    const row = document.createElement('tr');
                    const status = user.is_active ? '<span class="badge bg-success">啟用</span>' : '<span class="badge bg-danger">停權</span>';
                    row.innerHTML = `
                        <td>${user.id}</td>
                        <td>${user.name}</td>
                        <td>${user.email || 'N/A'}</td>
                        <td>${user.role}</td>
                        <td>${status}</td>
                        <td>
                            <a href="/admin/user/${user.id}" class="btn btn-sm btn-primary">詳情</a>
                        </td>
                    `;
                    usersTableBody.appendChild(row);
                });
            } catch (e) { showStatus(`無法載入使用者: ${e.message}`, true); }
        };
        
        // 載入匯率
        const ratesListDiv = document.getElementById('manual-rates-list');
        const loadManualRates = async () => {
            try {
                const res = await fetch('/api/admin/manual-rates');
                const data = await res.json();
                ratesListDiv.innerHTML = '';
                if (data.success && Object.keys(data.rates).length > 0) {
                    for (const [key, value] of Object.entries(data.rates)) {
                        addRatePairToDOM(key, value);
                    }
                } else {
                    addRatePairToDOM('USD_TWD', '');
                }
            } catch (e) { showStatus('載入匯率失敗', true); }
        };
        
        const addRatePairToDOM = (key = '', value = '') => {
            const div = document.createElement('div');
            div.className = 'input-group mb-2';
            div.innerHTML = `
                <input type="text" class="form-control manual-rate-key" value="${key}" placeholder="USD_TWD">
                <input type="number" class="form-control manual-rate-value" value="${value}" placeholder="匯率">
                <button class="btn btn-outline-danger btn-remove-rate" type="button">X</button>
            `;
            ratesListDiv.appendChild(div);
            div.querySelector('.btn-remove-rate').addEventListener('click', () => div.remove());
        };
        
        document.getElementById('btn-add-rate-pair').addEventListener('click', () => addRatePairToDOM());
        
        document.getElementById('btn-save-rates').addEventListener('click', async () => {
            const rates = {};
            const keys = document.querySelectorAll('.manual-rate-key');
            const values = document.querySelectorAll('.manual-rate-value');
            
            keys.forEach((keyInput, index) => {
                const key = keyInput.value.trim().toUpperCase();
                const value = parseFloat(values[index].value);
                if (key && value > 0) {
                    rates[key] = value;
                }
            });
            
            try {
                const res = await fetch('/api/admin/manual-rates', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ rates: rates })
                });
                const result = await res.json();
                if (result.success) showStatus('手動匯率已儲存', false);
                else showStatus(`儲存失敗: ${result.error}`, true);
            } catch (e) { showStatus(`儲存失敗: ${e.message}`, true); }
        });

        // 初始載入
        loadStats();
        loadUsers();
        loadManualRates();
    }


    // --- 使用者詳情頁 (admin_user_detail.html) ---
    if (document.getElementById('detail-user-id')) {
        
        const userIdInput = document.getElementById('detail-user-id');
        const userNameSpan = document.getElementById('detail-user-name');
        const emailInput = document.getElementById('detail-email');
        const roleSelect = document.getElementById('detail-role');
        const isActiveCheck = document.getElementById('detail-is-active');
        const walletsList = document.getElementById('detail-wallets-list');
        const transactionsList = document.getElementById('detail-transactions-list');
        const adjCurrencySelect = document.getElementById('adj-currency');
        const monthFilterInput = document.getElementById('admin-tx-month-filter'); // (*** (新) ***)

        // 從 URL 取得 User ID
        const pathParts = window.location.pathname.split('/');
        const USER_ID = pathParts[pathParts.length - 1];
        
        const loadUserDetails = async () => {
            if (!USER_ID) return;
            try {
                const res = await fetch(`/api/admin/user/${USER_ID}`);
                const data = await res.json();
                if (!data.success) {
                    showStatus(data.error, true); return;
                }
                
                const user = data.user_data;
                userIdInput.value = user.id;
                userNameSpan.textContent = user.name;
                emailInput.value = user.email || '';
                roleSelect.value = user.role;
                isActiveCheck.checked = user.is_active;
                
                // 錢包
                walletsList.innerHTML = '';
                adjCurrencySelect.innerHTML = '';
                if (user.wallets.length > 0) {
                    user.wallets.forEach(w => {
                        walletsList.innerHTML += `<li class="list-group-item">${w.currency}: <strong>${w.balance.toFixed(2)}</strong></li>`;
                        adjCurrencySelect.innerHTML += `<option value="${w.currency}">${w.currency}</option>`;
                    });
                } else {
                    walletsList.innerHTML = '<li class="list-group-item">無錢包</li>';
                }
                // 補上 TWD (用於手動開戶)
                if (!user.wallets.find(w => w.currency === 'TWD')) {
                    adjCurrencySelect.innerHTML += '<option value="TWD">TWD (新)</option>';
                }

                // (*** (新) 交易紀錄改為獨立載入 ***)

            } catch (e) { showStatus(`載入使用者資料失敗: ${e.message}`, true); }
        };
        
        // (*** (新) 獨立載入交易紀錄函式 (Req 5A) ***)
        const loadUserTransactions = async (userId, month) => {
            let apiUrl = `/api/admin/user/${userId}/transactions`;
            if (month) {
                apiUrl += `?month=${month}`;
            }
            try {
                const res = await fetch(apiUrl);
                const transactions = await res.json();
                transactionsList.innerHTML = '';
                if (transactions.length > 0) {
                    transactions.forEach(tx => {
                        transactionsList.innerHTML += `
                            <tr>
                                <td>${tx.date}</td>
                                <td>${tx.type}</td>
                                <td>${tx.currency}</td>
                                <td class="${tx.amount > 0 ? 'text-success' : 'text-danger'}">${tx.amount.toFixed(2)}</td>
                                <td>${tx.note || ''}</td>
                            </tr>
                        `;
                    });
                } else {
                    transactionsList.innerHTML = '<tr><td colspan="5" class="text-center">沒有交易紀錄</td></tr>';
                }
            } catch (e) {
                transactionsList.innerHTML = `<tr><td colspan="5" class="text-danger">載入失敗: ${e.message}</td></tr>`;
            }
        };

        
        // 儲存變更
        document.getElementById('btn-update-user').addEventListener('click', async () => {
            const payload = {
                email: emailInput.value,
                role: roleSelect.value,
                is_active: isActiveCheck.checked
            };
            
            try {
                const res = await fetch(`/api/admin/user/${USER_ID}/update`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await res.json();
                if (result.success) showStatus('使用者資料已更新', false);
                else showStatus(`更新失敗: ${result.error}`, true);
            } catch (e) { showStatus(`更新失敗: ${e.message}`, true); }
        });
        
        // 重設密碼
        document.getElementById('btn-reset-password').addEventListener('click', async () => {
            if (!confirm(`確定要為 ${userNameSpan.textContent} 重設密碼嗎？\n新密碼將會透過 Email (如果存在) 寄出。`)) return;
            
             try {
                const res = await fetch(`/api/admin/user/${USER_ID}/reset-password`, { method: 'POST' });
                const result = await res.json();
                if (result.success) {
                    showStatus(`密碼已重設為: ${result.new_password} (請手動轉告或檢查 Email)`, false);
                } else showStatus(`重設失敗: ${result.error}`, true);
            } catch (e) { showStatus(`重設失敗: ${e.message}`, true); }
        });

        // 手動調整
        document.getElementById('btn-manual-adjust').addEventListener('click', async () => {
            const payload = {
                user_id: USER_ID,
                currency: document.getElementById('adj-currency').value,
                amount: parseFloat(document.getElementById('adj-amount').value),
                note: document.getElementById('adj-note').value
            };
            
            if (!payload.currency || !payload.amount || !payload.note) {
                showStatus('幣別、金額和備註皆為必填', true); return;
            }
            if (payload.amount === 0) {
                showStatus('金額不能為 0', true); return;
            }
            
            const action = payload.amount > 0 ? '存入' : '提出';
            if (!confirm(`確定要為 ${userNameSpan.textContent} ${action} ${payload.currency} ${Math.abs(payload.amount)} 嗎？`)) return;

            try {
                const res = await fetch('/api/admin/manual-adjustment', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await res.json();
                if (result.success) {
                    showStatus('帳務調整成功', false);
                    loadUserDetails(); // 重新載入錢包
                    loadUserTransactions(USER_ID, monthFilterInput.value); // 重新載入交易
                } else showStatus(`調整失敗: ${result.error}`, true);
            } catch (e) { showStatus(`調整失敗: ${e.message}`, true); }
        });

        // (*** (新) 綁定月份篩選 (Req 5A) ***)
        monthFilterInput.addEventListener('change', () => {
            loadUserTransactions(USER_ID, monthFilterInput.value);
        });

        // 初始載入
        loadUserDetails();
        loadUserTransactions(USER_ID, null); // 載入所有交易
    }
});