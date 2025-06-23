const API_ROUTE_LOGIN = 'http://localhost:3030/api/login';

function showAlertBanner(message) {
    const alertBanner = document.getElementById('alert-banner');
    alertBanner.classList.remove('d-none');
    alertBanner.querySelector('#alert-banner-text').innerText = message;
    setTimeout(() => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }, 200);
};

// Function to handle the login process with error banner and redirect the user
async function loginHandler() {
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const next = document.getElementById('next').value;
    if (!email || !password) {
        showAlertBanner('Please fill in all fields');
        return;
    }
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({email, password, next}),
            credentials: 'include',
        });
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        else {
            const data = await response.json();
            if (data.error) {
                showAlertBanner(data.error);
                return;
            }
            else {
                var next_url = data.url;
            }
        }
        
        const apiResponse = await fetch(API_ROUTE_LOGIN, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({email, password})
        });
        
        if (!apiResponse.ok) {
            throw new Error('API response was not ok');
        }
        
        window.location.href=next_url
    }
    catch (error) {
        showAlertBanner('Login failed. Please try again.');
        console.error('Error', error);
        return;
    }
}

// Event listener for the login form submission
document.getElementById('login-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    await loginHandler();
});