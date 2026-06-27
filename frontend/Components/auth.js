/**
 * components/auth.js - Authentication handling
 * 
 * Manages login and registration forms.
 */

function initAuth() {
    // Tab switching
    document.querySelectorAll('.auth-tabs .tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            
            // Update active tab
            document.querySelectorAll('.auth-tabs .tab-btn').forEach(b => {
                b.classList.toggle('active', b.dataset.tab === tab);
            });
            
            // Show/hide forms
            document.getElementById('login-form').classList.toggle('hidden', tab !== 'login');
            document.getElementById('register-form').classList.toggle('hidden', tab !== 'register');
        });
    });
    
    // Login form
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const errorEl = document.getElementById('login-error');
        errorEl.textContent = '';
        
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        
        try {
            // OAuth2 password flow uses form data
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);
            
            // const response = await fetch(`${API_BASE_URL}/api/users/login`, {
            //     method: 'POST',
            //     body: formData
            // });

            // const data = await response.json();

            const response = await fetch(`${API_BASE_URL}/api/users/login`, {
                    method: "POST",
                    body: formData
            });

            console.log(API_BASE_URL);
            console.log(`${API_BASE_URL}/api/users/login`);

            const text = await response.text();
            console.log("Response:", text);

            const data = text ? JSON.parse(text) : {};
            console.log(data);
            
            
            
            if (!response.ok) {
                throw new Error(data.detail || 'Login failed');
            }
            
            // Save token and load user
            AppState.token = data.access_token;
            localStorage.setItem('token', data.access_token);
            
            await checkAuth();
            
        } catch (error) {
            errorEl.textContent = error.message;
        }
    });
    
    // Register form
    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const errorEl = document.getElementById('register-error');
        errorEl.textContent = '';
        
        const email = document.getElementById('register-email').value;
        const password = document.getElementById('register-password').value;
        
        try {
            await apiRequest('/api/users/register', {
                method: 'POST',
                body: { email, password }
            });
            
            // Auto-login after registration
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);
            
            const response = await fetch(`${API_BASE_URL}/api/users/login`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            AppState.token = data.access_token;
            localStorage.setItem('token', data.access_token);
            
            await checkAuth();
            
        } catch (error) {
            errorEl.textContent = error.message;
        }
    });
}
