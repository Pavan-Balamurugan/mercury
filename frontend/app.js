const USER_API = "http://localhost:8001";
const PRODUCT_API = "http://localhost:8002";
const INVENTORY_API = "http://localhost:8003";
const ORDER_API = "http://localhost:8004";

let token = null;
let userId = null;
let orders = [];

const logEl = document.getElementById("log");
function log(msg, isErr = false) {
  const time = new Date().toLocaleTimeString();
  const line = document.createElement("span");
  line.className = "line" + (isErr ? " err" : "");
  line.innerHTML = `<span class="ts">${time}</span>${msg}`;
  logEl.insertBefore(line, logEl.querySelector(".cursor"));
  logEl.scrollTop = logEl.scrollHeight;
}

async function api(url, options = {}) {
  const headers = options.headers || {};
  headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const resp = await fetch(url, { ...options, headers });
  if (!resp.ok) {
    const body = await resp.text();
    throw new Error(`${resp.status}: ${body}`);
  }
  if (resp.status === 204) return null;
  return resp.json();
}

// ---- health strip ----
async function checkHealth() {
  const services = [
    { key: "user", url: `${USER_API}/health` },
    { key: "product", url: `${PRODUCT_API}/health` },
    { key: "inventory", url: `${INVENTORY_API}/health` },
    { key: "order", url: `${ORDER_API}/health` },
  ];
  for (const s of services) {
    const dot = document.querySelector(`.health-dot[data-svc="${s.key}"]`);
    try {
      const resp = await fetch(s.url);
      dot.classList.toggle("up", resp.ok);
      dot.classList.toggle("down", !resp.ok);
    } catch (_) {
      dot.classList.add("down");
      dot.classList.remove("up");
    }
  }
}

// ---- auth ----
document.getElementById("registerBtn").onclick = async () => {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  try {
    await api(`${USER_API}/auth/register`, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    log(`registered <b>${email}</b>`);
  } catch (e) {
    log(`register failed — ${e.message}`, true);
  }
};

document.getElementById("loginBtn").onclick = async () => {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  try {
    const data = await api(`${USER_API}/auth/login`, {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    token = data.access_token;
    const me = await api(`${USER_API}/auth/me`);
    userId = me.id;
    document.getElementById("authStatus").textContent = me.email;
    log(`session established for <b>${me.email}</b>`);
  } catch (e) {
    log(`login failed — ${e.message}`, true);
  }
};

// ---- products ----
document.getElementById("addProductBtn").onclick = async () => {
  const name = document.getElementById("newProductName").value;
  const price = parseFloat(document.getElementById("newProductPrice").value);
  const category = document.getElementById("newProductCategory").value;
  const stock = parseInt(document.getElementById("newProductStock").value || "0", 10);
  if (!name || isNaN(price)) {
    log(`add product failed — name and price required`, true);
    return;
  }
  try {
    const product = await api(`${PRODUCT_API}/products`, {
      method: "POST",
      body: JSON.stringify({ name, price, category }),
    });
    await api(`${INVENTORY_API}/inventory/${product.id}`, {
      method: "PUT",
      body: JSON.stringify({ available_qty: stock }),
    });
    log(`catalog: added <b>${name}</b> (stock ${stock})`);
    document.getElementById("newProductName").value = "";
    document.getElementById("newProductPrice").value = "";
    document.getElementById("newProductCategory").value = "";
    document.getElementById("newProductStock").value = "";
    loadProducts();
  } catch (e) {
    log(`add product failed — ${e.message}`, true);
  }
};

async function loadProducts() {
  const grid = document.getElementById("productGrid");
  try {
    const products = await api(`${PRODUCT_API}/products/search`);
    if (products.length === 0) {
      grid.innerHTML = `<p class="empty-state">Catalog is empty. Add a product above.</p>`;
      return;
    }
    grid.innerHTML = "";
    for (const p of products) {
      let stock = { available_qty: "?" };
      try {
        stock = await api(`${INVENTORY_API}/inventory/${p.id}`);
      } catch (_) {}

      const card = document.createElement("div");
      card.className = "product-card";
      card.innerHTML = `
        <div class="p-category">${p.category || "uncategorized"}</div>
        <div class="p-name">${p.name}</div>
        <div class="p-meta">
          <span class="p-price">₹${p.price}</span>
          <span class="p-stock">${stock.available_qty} in stock</span>
        </div>
        <div class="p-order-row">
          <input type="number" min="1" value="1" id="qty-${p.id}">
          <button class="btn-primary small" data-id="${p.id}">Order</button>
        </div>
      `;
      card.querySelector("button").onclick = () => placeOrder(p.id);
      grid.appendChild(card);
    }
  } catch (e) {
    log(`load catalog failed — ${e.message}`, true);
  }
}

// ---- orders ----
async function placeOrder(productId) {
  if (!userId) {
    log(`order blocked — log in first`, true);
    return;
  }
  const qty = parseInt(document.getElementById(`qty-${productId}`).value || "1", 10);
  try {
    const order = await api(`${ORDER_API}/orders`, {
      method: "POST",
      body: JSON.stringify({
        user_id: userId,
        items: [{ product_id: productId, quantity: qty }],
      }),
    });
    log(`order <b>${order.id.slice(0, 8)}</b> placed — status ${order.status}`);
    orders.unshift(order.id);
    renderOrders();
    loadProducts();
  } catch (e) {
    log(`order failed — ${e.message}`, true);
  }
}

const STAGES = ["PENDING", "PAYMENT_PENDING", "CONFIRMED"];

function pipelineHTML(status) {
  const failed = status === "FAILED" || status === "PAYMENT_FAILED";
  const currentIdx = STAGES.indexOf(status);

  let html = `<div class="pipeline">`;
  STAGES.forEach((stage, i) => {
    let cls = "stage";
    if (failed && i === currentIdx + 1) {
      cls += " failed";
    } else if (currentIdx === -1) {
      // unknown/failed before reaching this stage
    } else if (i < currentIdx) {
      cls += " done";
    } else if (i === currentIdx) {
      cls += status === "CONFIRMED" ? " done" : " active";
    }
    html += `<span class="${cls}">${stage}</span>`;
    if (i < STAGES.length - 1) {
      const connDone = i < currentIdx;
      html += `<span class="connector${connDone ? " done" : ""}"></span>`;
    }
  });
  html += `</div>`;

  if (failed) {
    html += `<div class="pipeline" style="margin-top:6px">
      <span class="stage failed">${status}</span>
    </div>`;
  }
  return html;
}

async function renderOrders() {
  const list = document.getElementById("orderList");
  if (orders.length === 0) {
    list.innerHTML = `<p class="empty-state">No orders placed yet. Add a product to the catalog, then order it.</p>`;
    return;
  }
  list.innerHTML = "";
  for (const id of orders) {
    let order;
    try {
      order = await api(`${ORDER_API}/orders/${id}`);
    } catch (_) {
      continue;
    }
    const itemsStr = order.items.map(i => `${i.quantity}× ${i.product_id.slice(0, 8)}`).join(", ");
    const card = document.createElement("div");
    card.className = "order-card";
    card.innerHTML = `
      <div class="order-id">ORDER ${order.id.slice(0, 8)}</div>
      <div class="order-items">${itemsStr}</div>
      ${pipelineHTML(order.status)}
    `;
    list.appendChild(card);
  }
}

document.getElementById("refreshOrdersBtn").onclick = () => {
  renderOrders();
  loadProducts();
  checkHealth();
};

// init
checkHealth();
setInterval(checkHealth, 10000);
loadProducts();