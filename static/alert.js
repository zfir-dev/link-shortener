function showAlert(message, type) {
  const modal = document.getElementById("alertModal");
  const modalTitle = document.getElementById("alertModalTitle");
  const modalMessage = document.getElementById("alertModalMessage");
  const modalButton = document.getElementById("alertModalButton");

  if (type === "success") {
    modalTitle.textContent = "Success";
    modalButton.classList.remove(
      "bg-red-600",
      "hover:bg-red-700",
      "text-red-900"
    );
    modalButton.classList.add(
      "bg-green-600",
      "hover:bg-green-700",
      "text-white"
    );
  } else if (type === "error") {
    modalTitle.textContent = "Error";
    modalButton.classList.remove(
      "bg-green-600",
      "hover:bg-green-700",
      "text-white"
    );
    modalButton.classList.add("bg-red-600", "hover:bg-red-700", "text-red-900");
  }

  modalMessage.textContent = message;

  modalButton.addEventListener("click", function () {
    modal.classList.add("hidden");
  });

  modal.classList.remove("hidden");
}
