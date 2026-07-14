const productGrid = document.querySelector("#marketplace-products");
const productCount = document.querySelector("#marketplace-product-count");
const searchForm = document.querySelector("#product-search-form");
const searchInput = document.querySelector("#product-search");
const clearSearchButton = document.querySelector("#clear-search");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderProducts(products) {
  productCount.textContent = `${products.length} product${products.length === 1 ? "" : "s"}`;

  if (products.length === 0) {
    productGrid.innerHTML = '<article class="product-card"><p>No matching products found.</p></article>';
    return;
  }

  productGrid.innerHTML = products
    .map(
      (product) => `
        <article class="product-card">
          <div class="product-card-header">
            <div>
              <h3>${escapeHtml(product.name)}</h3>
              <p>${escapeHtml(product.brand)}</p>
            </div>
          </div>
          <dl class="product-meta">
            <div>
              <dt>Importer</dt>
              <dd>
                ${escapeHtml(product.importerBusinessName)}
                <span class="status-badge inline-badge">${escapeHtml(product.importerVerificationStatus)}</span>
              </dd>
            </div>
            <div>
              <dt>Batch</dt>
              <dd>${escapeHtml(product.batchNumber)}</dd>
            </div>
            <div>
              <dt>Expiry</dt>
              <dd>${escapeHtml(product.expiryDate)}</dd>
            </div>
          </dl>
          <button class="button primary quote-button" type="button" data-product-id="${product.id}">
            Request Quote
          </button>
          <p class="quote-message" data-message-for="${product.id}" role="status"></p>
        </article>
      `
    )
    .join("");
}

async function loadProducts() {
  const search = searchInput.value.trim();
  const query = search ? `?search=${encodeURIComponent(search)}` : "";
  const response = await fetch(`/api/pharmacy/products${query}`);
  const data = await response.json();

  if (!response.ok) {
    productGrid.innerHTML = `<article class="product-card"><p>${escapeHtml(data.message || "Could not load products.")}</p></article>`;
    productCount.textContent = "Unavailable";
    return;
  }

  renderProducts(data);
}

async function requestQuote(productId, button) {
  const message = document.querySelector(`[data-message-for="${productId}"]`);
  button.disabled = true;
  message.textContent = "Submitting request...";
  message.classList.remove("error");

  const response = await fetch("/api/pharmacy/quote-request", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ productId }),
  });
  const data = await response.json();

  if (!response.ok) {
    message.textContent = data.message || "Could not submit quote request.";
    message.classList.add("error");
    button.disabled = false;
    return;
  }

  message.textContent = "Quote request submitted.";
  button.textContent = "Requested";
}

searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  loadProducts();
});

clearSearchButton.addEventListener("click", () => {
  searchInput.value = "";
  loadProducts();
});

productGrid.addEventListener("click", (event) => {
  const button = event.target.closest(".quote-button");
  if (!button) {
    return;
  }

  requestQuote(Number(button.dataset.productId), button);
});

loadProducts();
