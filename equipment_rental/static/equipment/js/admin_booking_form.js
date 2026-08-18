document.addEventListener("DOMContentLoaded", function () {
    const statusForm = document.querySelector(".status-form");
    const submitButton = document.querySelector(".btn-submit");
    const cancelButton = document.querySelector(".btn-cancel");

    const bookingStatusSelect = document.querySelector('select[name="booking_status"]');
    const paymentStatusSelect = document.querySelector('select[name="payment_status"]');
    const adminNotes = document.querySelector('textarea[name="booking_notes"]');

    const alerts = document.querySelectorAll(".alert");

    function autoHideAlerts() {
        alerts.forEach(function (alertBox) {
            setTimeout(function () {
                alertBox.style.transition = "all 0.5s ease";
                alertBox.style.opacity = "0";
                alertBox.style.transform = "translateY(-10px)";

                setTimeout(function () {
                    alertBox.remove();
                }, 500);
            }, 4000);
        });
    }

    function clearError(field) {
        if (!field) {
            return;
        }

        field.classList.remove("is-invalid");

        const oldError = field.parentElement.querySelector(".custom-error");

        if (oldError) {
            oldError.remove();
        }
    }

    function showError(field, message) {
        if (!field) {
            return;
        }

        clearError(field);

        field.classList.add("is-invalid");

        const errorBox = document.createElement("div");
        errorBox.className = "invalid-feedback custom-error";
        errorBox.textContent = message;

        field.parentElement.appendChild(errorBox);
    }

    function validateStatusFields() {
        let isValid = true;

        clearError(bookingStatusSelect);
        clearError(paymentStatusSelect);

        if (!bookingStatusSelect || !bookingStatusSelect.value.trim()) {
            showError(bookingStatusSelect, "Booking status is required.");
            isValid = false;
        }

        if (!paymentStatusSelect || !paymentStatusSelect.value.trim()) {
            showError(paymentStatusSelect, "Payment status is required.");
            isValid = false;
        }

        return isValid;
    }

    function validateStatusCombination() {
        if (!bookingStatusSelect || !paymentStatusSelect) {
            return true;
        }

        const bookingStatus = bookingStatusSelect.value;
        const paymentStatus = paymentStatusSelect.value;

        clearError(bookingStatusSelect);
        clearError(paymentStatusSelect);

        if (bookingStatus === "confirmed" && paymentStatus !== "paid") {
            showError(paymentStatusSelect, "Confirmed booking should have paid payment status.");
            return false;
        }

        if (bookingStatus === "completed" && paymentStatus !== "paid") {
            showError(paymentStatusSelect, "Completed booking should have paid payment status.");
            return false;
        }

        if (paymentStatus === "paid" && bookingStatus === "cancelled") {
            showError(bookingStatusSelect, "Paid booking should not be cancelled directly.");
            return false;
        }

        return true;
    }

    function validateNotesLength() {
        if (!adminNotes) {
            return true;
        }

        clearError(adminNotes);

        const notes = adminNotes.value.trim();

        if (notes.length > 1000) {
            showError(adminNotes, "Admin notes cannot be more than 1000 characters.");
            return false;
        }

        return true;
    }

    function validateForm() {
        const statusValid = validateStatusFields();
        const combinationValid = validateStatusCombination();
        const notesValid = validateNotesLength();

        return statusValid && combinationValid && notesValid;
    }

    function updateStatusPreview() {
        if (!bookingStatusSelect || !paymentStatusSelect) {
            return;
        }

        const bookingBadge = document.querySelector(".status-badge");
        const paymentBadge = document.querySelector(".payment-badge");

        if (bookingBadge) {
            bookingBadge.className = "status-badge " + bookingStatusSelect.value;
            bookingBadge.textContent =
                bookingStatusSelect.options[bookingStatusSelect.selectedIndex].text;
        }

        if (paymentBadge) {
            paymentBadge.className = "payment-badge " + paymentStatusSelect.value;
            paymentBadge.textContent =
                paymentStatusSelect.options[paymentStatusSelect.selectedIndex].text;
        }
    }

    function setSubmitLoading() {
        if (!submitButton) {
            return;
        }

        submitButton.disabled = true;
        submitButton.innerHTML =
            '<i class="fas fa-spinner fa-spin"></i> Updating...';
    }

    if (bookingStatusSelect) {
        bookingStatusSelect.addEventListener("change", function () {
            clearError(bookingStatusSelect);
            updateStatusPreview();
        });
    }

    if (paymentStatusSelect) {
        paymentStatusSelect.addEventListener("change", function () {
            clearError(paymentStatusSelect);
            updateStatusPreview();
        });
    }

    if (adminNotes) {
        adminNotes.addEventListener("input", function () {
            clearError(adminNotes);
        });
    }

    if (statusForm) {
        statusForm.addEventListener("submit", function (event) {
            if (!validateForm()) {
                event.preventDefault();
                event.stopPropagation();
                return;
            }

            const confirmed = confirm("Are you sure you want to update this booking?");

            if (!confirmed) {
                event.preventDefault();
                return;
            }

            setSubmitLoading();
        });
    }

    if (cancelButton) {
        cancelButton.addEventListener("click", function () {
            cancelButton.style.transform = "scale(0.96)";

            setTimeout(function () {
                cancelButton.style.transform = "";
            }, 150);
        });
    }

    autoHideAlerts();
    updateStatusPreview();
});