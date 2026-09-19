requireAuth();
renderNav("orders");

const STAGES = ["PENDING", "PAYMENT_PENDING", "CONFIRMED"];

function pipelineHTML(status) {
  const failed = status === "FAILED" || status === "PAYMENT_FAILED";
  const currentIdx = STAGES.indexOf(status);

  let html = `<div class="pipeline">`;
  STAGES.forEach((stage, i) => {
    let cls = "stage";
    if (failed && i === currentIdx + 1) {
      cls += " failed";
    } else if (currentIdx !== -1 && i < currentIdx) {
      cls += " done";
    } else if (i === currentIdx) {
      cls += status === "CONFIRMED" ? " done" : " active";
    }
    html += `<span class="${cls}">${stage}</span>`;
    if (i < STAGES.length - 1) {
      const connDone = currentIdx !== -1 && i < currentIdx;
      html += `<span class="connector${connDone ? " done" : ""}"></span>`;
    }
  });
  html += `</div>`;

  if (failed) {
    html += `<div class="pipeline" style="margin-top:6px"><span class="stage failed">${status}</span></div>`;
  }
  return html;
}

async function renderOrders() {
  const list = document.getElementById("orderList");
  const orderIds = getTrackedOrders();
  if (orderIds.length === 0) {
    list.innerHTML = `<p class="empty-state">No orders placed yet. Visit the Catalog to order something.</p>`;
    return;
  }
  list.innerHTML = "";
  for (const id of orderIds) {
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

document.getElementById("refreshBtn").onclick = renderOrders;
renderOrders();
