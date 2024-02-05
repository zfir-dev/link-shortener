function showAlert(message, type) {
    const modal = document.getElementById("alertModal");
    const modalTitle = document.getElementById("alertModalTitle");
    const modalMessage = document.getElementById("alertModalMessage");
    const modalButton = document.getElementById("alertModalButton");

    if (type === "success") {
        modalTitle.textContent = "Success";
        modalButton.classList.remove("bg-red-600", "hover:bg-red-700", "text-red-900");
        modalButton.classList.add("bg-green-600", "hover:bg-green-700", "text-white");
    } else if (type === "error") {
        modalTitle.textContent = "Error";
        modalButton.classList.remove("bg-green-600", "hover:bg-green-700", "text-white");
        modalButton.classList.add("bg-red-600", "hover:bg-red-700", "text-red-900");
    }

    modalMessage.textContent = message;

    modalButton.addEventListener("click", function () {
        modal.classList.add("hidden");
    });

    modal.classList.remove("hidden");
}

function showConfirmationAlert(title, message, confirmLabel, cancelLabel, confirmCallback) {
    const modal = document.getElementById("confirmationModal");
    const modalTitle = document.getElementById("confirmationModalTitle");
    const modalMessage = document.getElementById("confirmationModalMessage");
    const modalConfirmButton = document.getElementById("confirmationModalConfirm");
    const modalCancelButton = document.getElementById("confirmationModalCancel");
    const modalCloseButton = document.getElementById("confirmationModalClose");

    modalTitle.textContent = title || "Confirmation";
    modalMessage.textContent = message || "Are you sure?";
    modalConfirmButton.textContent = confirmLabel || "Confirm";
    modalCancelButton.textContent = cancelLabel || "Cancel";

    modalConfirmButton.addEventListener("click", function () {
        if (typeof confirmCallback === "function") {
            confirmCallback();
        }

        modal.classList.add("hidden");
    });

    modalCancelButton.addEventListener("click", function () {
        modal.classList.add("hidden");
    });

    modalCloseButton.addEventListener("click", function () {
        modal.classList.add("hidden");
    });

    modal.classList.remove("hidden");
}
