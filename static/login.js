document.addEventListener('DOMContentLoaded', () => {
    
    const statusDiv = document.getElementById('status-message');

    function showStatus(message, isError = false) {
        if (isError) {
            statusDiv.className = 'alert alert-danger';
        } else {
            statusDiv.className = 'alert alert-success';
        }
        statusDiv.innerText = message;
    }

    // 處理登入表單
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault(); // 防止表單傳統提交
            const name = document.getElementById('login-name').value;
            const password = document.getElementById('login-password').value;

            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, password })
            });
            const result = await response.json();

            if (result.success) {
                showStatus('登入成功！正在跳轉...', false);
                window.location.href = '/'; // 登入成功，跳轉到主頁面
            } else {
                showStatus(`登入失敗: ${result.error}`, true);
            }
        });
    }

    // 處理註冊表單
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('reg-name').value;
            const password = document.getElementById('reg-password').value;
            const amount = document.getElementById('reg-amount').value;

            const response = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, password, amount })
            });
            const result = await response.json();

            if (result.success) {
                showStatus('註冊成功！請返回登入。', false);
            } else {
                showStatus(`註冊失敗: ${result.error}`, true);
            }
        });
    }
});