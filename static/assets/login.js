async function checkLoginStatus() {
    try {
        const response = await fetch('/login/status');
        const data = await response.json();
        if (response.status === 200) {
            window.location.href = '/linked';
        } else if (response.status === 401 && data.status === 'fail') {
            window.location.href = '/error';
        } else {
            setTimeout(checkLoginStatus, 800);
        }
    } catch (error) {
        console.error('Error checking login status:', error);
        setTimeout(checkLoginStatus, 1000);
    }
}
checkLoginStatus();
