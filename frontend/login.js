renderNav(null);

// If already logged in, skip straight to catalog.
if (getSession()) {
  window.location.href = "catalog.html";
}

const errorEl = document.getElementById("errorMsg");

function showError(msg) {
  errorEl.textContent = msg;
}

document.getElementById("registerBtn").onclick = async () => {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  if (!email || !password) {
    showError("Email and password are required.");
    return;
  }
  try {
    await api(`${USER_API}/auth/register`, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    showError("Account created. Now click Login.");
  } catch (e) {
    showError(e.message);
  }
};

document.getElementById("loginBtn").onclick = async () => {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  if (!email || !password) {
    showError("Email and password are required.");
    return;
  }
  try {
    const data = await api(`${USER_API}/auth/login`, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setSession(data.access_token, null, email);
    const me = await api(`${USER_API}/auth/me`);
    setSession(data.access_token, me.id, me.email);
    window.location.href = "catalog.html";
  } catch (e) {
    showError(e.message);
  }
};
