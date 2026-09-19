const session = requireAuth();
renderNav("catalog");

document.getElementById("addProductBtn").onclick = async () => {
  const name = document.getElementById("newProductName").value;
  const price = parseFloat(document.getElementById("newProductPrice").value);
  const category = document.getElementById("newProductCategory").value;
  const stock = parseInt(document.getElementById("newProductStock").value || "0", 10);
  if (!name || isNaN(price)) return;
  try {
    const product = await api(`${PRODUCT_API}/products`, {
      method: "POST",
      body: JSON.stringify({ name, price, category }),
    });
    await api(`${INVENTORY_API}/inventory/${product.id}`, {
      method: "PUT",
      body: JSON.stringify({ available_qty: stock }),
    });
    document.getElementById("newProductName").value = "";
    document.getElementById("newProductPrice").value = "";
    document.getElementById("newProductCategory").value = "";
    document.getElementById("newProductStock").value = "";
    loadProducts();
  } catch (e) {
    alert(`Add product failed: ${e.message}`);
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
          <button class="btn-primary small" style="width:auto" data-id="${p.id}">Order</button>
        </div>
      `;
      card.querySelector("button").onclick = () => placeOrder(p.id);
      grid.appendChild(card);
    }
  } catch (e) {
    console.error(e);
  }
}

async function placeOrder(productId) {
  const qty = parseInt(document.getElementById(`qty-${productId}`).value || "1", 10);
  try {
    const order = await api(`${ORDER_API}/orders`, {
      method: "POST",
      body: JSON.stringify({
        user_id: session.userId,
        items: [{ product_id: productId, quantity: qty }],
      }),
    });
    trackOrder(order.id);
    loadProducts();
    if (confirm(`Order placed — status: ${order.status}. View order pipeline now?`)) {
      window.location.href = "orders.html";
    }
  } catch (e) {
    alert(`Order failed: ${e.message}`);
  }
}

loadProducts();
