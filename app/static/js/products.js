const form = document.querySelector("#product-form");
const openFormButton = document.querySelector("#open-product-form");
const cancelFormButton = document.querySelector("#cancel-product-form");
const formMessage = document.querySelector("#form-message");
const tableBody = document.querySelector("#products-table-body");
const productCount = document.querySelector("#product-count");

function setFormVisible(isVisible) {
  form.classList.toggle("hidden", !isVisible);
  if (isVisible) {
    form.elements.name.focus();
  }
}

function clearErrors() {
  formMessage.textContent = "";
  formMessage.classList.remove("error");
  document.querySelectorAll("[data-error-for]").forEach((node) => {
    node.textContent = "";
  });
}

function renderProducts(products) {
  productCount.textContent = `${products.length} product${products.length === 1 ? "" : "s"}`;

  if (products.length === 0) {
    tableBody.innerHTML = '<tr><td colspan="5">No products have been added yet.</td></tr>';
    return;
  }

  tableBody.innerHTML = products
    .map(
      (product) => `
        <tr>
          <td>${escapeHtml(product.name)}</td>
          <td>${escapeHtml(product.brand)}</td>
          <td>${escapeHtml(product.batchNumber)}</td>
          <td>${escapeHtml(product.expiryDate)}</td>
          <td>${escapeHtml(product.status)}</td>
        </tr>
      `
    )
    .join("");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadProducts() {
  const response = await fetch("/api/importer/products");
  const data = await response.json();

  if (!response.ok) {
    tableBody.innerHTML = `<tr><td colspan="5">${escapeHtml(data.message || "Could not load products.")}</td></tr>`;
    productCount.textContent = "Unavailable";
    return;
  }

  renderProducts(data);
}

async function createProduct(event) {
  event.preventDefault();
  clearErrors();

  const formData = new FormData(form);
  const payload = {
    name: formData.get("name"),
    brand: formData.get("brand"),
    batchNumber: formData.get("batchNumber"),
    expiryDate: formData.get("expiryDate"),
  };

  const response = await fetch("/api/importer/products", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  const data = await response.json();

  if (!response.ok) {
    if (data.fields) {
      Object.entries(data.fields).forEach(([field, message]) => {
        const errorNode = document.querySelector(`[data-error-for="${field}"]`);
        if (errorNode) {
          errorNode.textContent = message;
        }
      });
    }
    formMessage.textContent = data.message || "Could not save product.";
    formMessage.classList.add("error");
    return;
  }

  form.reset();
  setFormVisible(false);
  formMessage.textContent = "";
  await loadProducts();
}

openFormButton.addEventListener("click", () => setFormVisible(true));
cancelFormButton.addEventListener("click", () => {
  form.reset();
  clearErrors();
  setFormVisible(false);
});
form.addEventListener("submit", createProduct);

loadProducts();

