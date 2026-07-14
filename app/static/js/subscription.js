async function startCheckout(planId, button) {
  const message = document.querySelector(`[data-plan-message="${planId}"]`);
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = "Processing...";
  message.textContent = "";
  message.classList.remove("error");

  const response = await fetch("/api/importer/subscription/checkout", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ planId }),
  });
  const data = await response.json();

  if (!response.ok) {
    message.textContent = data.message || "Could not start checkout.";
    message.classList.add("error");
    button.disabled = false;
    button.textContent = originalText;
    return;
  }

  if (data.checkoutUrl) {
    window.location.href = data.checkoutUrl;
    return;
  }

  message.textContent = data.message || "Subscription updated.";
  button.disabled = false;
  button.textContent = originalText;
}

document.addEventListener("click", (event) => {
  const button = event.target.closest(".subscription-checkout");
  if (!button) {
    return;
  }

  startCheckout(Number(button.dataset.planId), button);
});

