async function postAdminAction(endpoint, payload) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Admin action failed.");
  }

  return data;
}

document.addEventListener("click", async (event) => {
  const planButton = event.target.closest(".plan-update");
  if (planButton) {
    const planId = Number(planButton.dataset.planId);
    const priceInput = document.querySelector(`[data-price-for="${planId}"]`);
    const limitInput = document.querySelector(`[data-limit-for="${planId}"]`);
    const originalText = planButton.textContent;

    planButton.disabled = true;
    planButton.textContent = "Saving...";

    try {
      await postAdminAction("/api/admin/update-plan", {
        planId,
        priceMonthly: Number(priceInput.value),
        listingLimit: limitInput.value === "" ? "" : Number(limitInput.value),
      });
      window.location.reload();
    } catch (error) {
      planButton.disabled = false;
      planButton.textContent = originalText;
      alert(error.message);
    }
    return;
  }

  const button = event.target.closest(".admin-action");
  if (!button) {
    return;
  }

  button.disabled = true;
  const originalText = button.textContent;
  button.textContent = "Saving...";

  const payload = {};
  if (button.dataset.userType) {
    payload.userType = button.dataset.userType;
  }
  if (button.dataset.userId) {
    payload.userId = button.dataset.userId;
  }
  if (button.dataset.decision) {
    payload.decision = button.dataset.decision;
  }
  if (button.dataset.action) {
    payload.action = button.dataset.action;
  }
  if (button.dataset.productId) {
    payload.productId = Number(button.dataset.productId);
  }

  try {
    await postAdminAction(button.dataset.endpoint, payload);
    window.location.reload();
  } catch (error) {
    button.disabled = false;
    button.textContent = originalText;
    alert(error.message);
  }
});
