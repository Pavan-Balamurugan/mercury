const USER_API = "http://localhost:8001";
const PRODUCT_API = "http://localhost:8002";
const INVENTORY_API = "http://localhost:8003";
const ORDER_API = "http://localhost:8004";

function getSession() {
  const token = localStorage.getItem("mercury_token");
  const userId = localStorage.getItem("mercury_user_id");
  const email = localStorage.getItem("mercury_email");
  if (!token || !userId) return null;
  return { token, userId, email };
}

function setSession(token, userId, email) {
  localStorage.setItem("mercury_token", token);
  localStorage.setItem("mercury_user_id", userId);
  localStorage.setItem("mercury_email", email);
}

function clearSession() {
  localStorage.removeItem("mercury_token");
  localStorage.removeItem("mercury_user_id");
  localStorage.removeItem("mercury_email");
}

function requireAuth() {
  const session = getSession();
  if (!session) {
    window.location.href = "login.html";
    return null;
  }
  return session;
}

async function api(url, options = {}) {
  const session = getSession();
  const headers = options.headers || {};
  headers["Content-Type"] = "application/json";
  if (session) headers["Authorization"] = `Bearer ${session.token}`;
  const resp = await fetch(url, { ...options, headers });
  if (resp.status === 401) {
    clearSession();
    window.location.href = "login.html";
    throw new Error("Session expired");
  }
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`${resp.status}: ${body}`);
  }
  if (resp.status === 204) return null;
  return resp.json();
}

function renderNav(activePage) {
  const session = getSession();
  const root = document.getElementById("nav-root");
  if (!root) return;

  const links = [
    { href: "catalog.html", label: "Catalog", key: "catalog" },
    { href: "orders.html", label: "Orders", key: "orders" },
  ];

  const linksHTML = links
    .map(
      (l) =>
        `<a href="${l.href}" class="nav-link${l.key === activePage ? " active" : ""}">${l.label}</a>`
    )
    .join("");

  root.innerHTML = `
    <div class="brand">
      <span class="brand-mark">◆</span>
      <span class="brand-name">MERCURY</span>
    </div>
    <nav class="nav-links">${session ? linksHTML : ""}</nav>
    <div class="session">
      ${session ? `<span>${session.email}</span> <button class="btn-ghost small" id="logoutBtn">Logout</button>` : `<a href="login.html" class="nav-link">Login</a>`}
    </div>
  `;

  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.onclick = () => {
      clearSession();
      window.location.href = "login.html";
    };
  }
}

// ---- order tracking (client-side list, since API has no "my orders" endpoint) ----
function trackOrder(orderId) {
  const key = "mercury_orders";
  const list = JSON.parse(localStorage.getItem(key) || "[]");
  list.unshift(orderId);
  localStorage.setItem(key, JSON.stringify(list));
}

function getTrackedOrders() {
  return JSON.parse(localStorage.getItem("mercury_orders") || "[]");
}
