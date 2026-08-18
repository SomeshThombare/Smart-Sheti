document.addEventListener("DOMContentLoaded", function () {
    const bookingForm = document.getElementById("bookingForm");

    const startDateInput = document.getElementById("startDate");
    const endDateInput = document.getElementById("endDate");
    const createdDateInput = document.getElementById("createdDate");

    const pricePerDayInput = document.getElementById("pricePerDay");
    const pricePerDayText = document.getElementById("pricePerDayText");
    const pricePerDayBox = document.getElementById("pricePerDayBox");

    const totalDaysBox = document.getElementById("totalDays");
    const totalAmountBox = document.getElementById("totalAmount");

    const totalDaysInput = document.getElementById("totalDaysInput");
    const totalAmountInput = document.getElementById("totalAmountInput");

    const submitButton = document.querySelector(".btn-submit");

    function normalizeNumber(value) {
        const number = parseFloat(String(value || "0").replace(/,/g, ""));

        if (isNaN(number)) {
            return 0;
        }

        return number;
    }

    function formatCurrency(amount) {
        return "₹" + Number(amount || 0).toFixed(2);
    }

    function parseDate(value) {
        if (!value) {
            return null;
        }

        const date = new Date(value + "T00:00:00");

        if (isNaN(date.getTime())) {
            return null;
        }

        return date;
    }

    function calculateDays(startDate, endDate) {
        if (!startDate || !endDate) {
            return 0;
        }

        const oneDay = 24 * 60 * 60 * 1000;
        const difference = endDate.getTime() - startDate.getTime();

        if (difference < 0) {
            return 0;
        }

        return Math.floor(difference / oneDay) + 1;
    }

    function updateCalculation() {
        const pricePerDay = normalizeNumber(
            pricePerDayInput ? pricePerDayInput.value : "0"
        );

        const startDate = parseDate(startDateInput ? startDateInput.value : "");
        const endDate = parseDate(endDateInput ? endDateInput.value : "");

        const totalDays = calculateDays(startDate, endDate);
        const totalAmount = totalDays * pricePerDay;

        if (pricePerDayText) {
            pricePerDayText.textContent = pricePerDay.toFixed(2);
        }

        if (pricePerDayBox) {
            pricePerDayBox.textContent = formatCurrency(pricePerDay);
        }

        if (totalDaysBox) {
            totalDaysBox.textContent = totalDays;
        }

        if (totalAmountBox) {
            totalAmountBox.textContent = formatCurrency(totalAmount);
        }

        if (totalDaysInput) {
            totalDaysInput.value = totalDays;
        }

        if (totalAmountInput) {
            totalAmountInput.value = totalAmount.toFixed(2);
        }
    }

    function showFieldError(input, message) {
        if (!input) {
            return;
        }

        input.classList.add("is-invalid");

        let errorBox = input.parentElement.querySelector(".invalid-feedback");

        if (!errorBox) {
            errorBox = document.createElement("div");
            errorBox.className = "invalid-feedback";
            input.parentElement.appendChild(errorBox);
        }

        errorBox.textContent = message;
    }

    function clearFieldError(input) {
        if (!input) {
            return;
        }

        input.classList.remove("is-invalid");

        const errorBox = input.parentElement.querySelector(".invalid-feedback");

        if (errorBox) {
            errorBox.remove();
        }
    }

    function clearAllFieldErrors() {
        const invalidInputs = document.querySelectorAll(".is-invalid");

        invalidInputs.forEach(function (input) {
            clearFieldError(input);
        });
    }

    function validateDates() {
        clearFieldError(startDateInput);
        clearFieldError(endDateInput);

        const todayValue = createdDateInput ? createdDateInput.value : "";
        const todayDate = parseDate(todayValue);

        const startDate = parseDate(startDateInput ? startDateInput.value : "");
        const endDate = parseDate(endDateInput ? endDateInput.value : "");

        let isValid = true;

        if (!startDateInput || !startDateInput.value) {
            showFieldError(startDateInput, "Start date is required.");
            isValid = false;
        }

        if (!endDateInput || !endDateInput.value) {
            showFieldError(endDateInput, "End date is required.");
            isValid = false;
        }

        if (todayDate && startDate && startDate < todayDate) {
            showFieldError(startDateInput, "Start date cannot be before today.");
            isValid = false;
        }

        if (todayDate && endDate && endDate < todayDate) {
            showFieldError(endDateInput, "End date cannot be before today.");
            isValid = false;
        }

        if (startDate && endDate && endDate < startDate) {
            showFieldError(endDateInput, "End date cannot be before start date.");
            isValid = false;
        }

        updateCalculation();

        return isValid;
    }

    function validateRequiredFields() {
        let isValid = true;

        const requiredFields = bookingForm
            ? bookingForm.querySelectorAll("[required]")
            : [];

        requiredFields.forEach(function (field) {
            clearFieldError(field);

            if (!String(field.value || "").trim()) {
                showFieldError(field, "This field is required.");
                isValid = false;
            }
        });

        return isValid;
    }

    function validatePhoneNumber() {
        const phoneInput = bookingForm
            ? bookingForm.querySelector('[name="customer_phone_number"]')
            : null;

        if (!phoneInput) {
            return true;
        }

        clearFieldError(phoneInput);

        const phone = String(phoneInput.value || "").trim();
        const phonePattern = /^[6-9]\d{9}$/;

        if (!phone) {
            showFieldError(phoneInput, "Phone number is required.");
            return false;
        }

        if (!phonePattern.test(phone)) {
            showFieldError(phoneInput, "Enter valid 10 digit Indian mobile number.");
            return false;
        }

        return true;
    }

    function validateEmail() {
        const emailInput = bookingForm
            ? bookingForm.querySelector('[name="customer_email_address"]')
            : null;

        if (!emailInput || !emailInput.value.trim()) {
            return true;
        }

        clearFieldError(emailInput);

        const email = String(emailInput.value || "").trim();
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!emailPattern.test(email)) {
            showFieldError(emailInput, "Enter valid email address.");
            return false;
        }

        return true;
    }

    function validateAmount() {
        const totalDays = normalizeNumber(totalDaysInput ? totalDaysInput.value : "0");
        const totalAmount = normalizeNumber(totalAmountInput ? totalAmountInput.value : "0");

        if (totalDays <= 0 || totalAmount <= 0) {
            showFieldError(endDateInput, "Please select valid booking dates.");
            return false;
        }

        return true;
    }

    function validateForm() {
        clearAllFieldErrors();

        const requiredValid = validateRequiredFields();
        const dateValid = validateDates();
        const phoneValid = validatePhoneNumber();
        const emailValid = validateEmail();
        const amountValid = validateAmount();

        return requiredValid && dateValid && phoneValid && emailValid && amountValid;
    }

    function autoHideAlerts() {
        const alerts = document.querySelectorAll(".alert");

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

    if (startDateInput) {
        startDateInput.addEventListener("change", function () {
            if (endDateInput && startDateInput.value) {
                endDateInput.min = startDateInput.value;

                if (endDateInput.value && endDateInput.value < startDateInput.value) {
                    endDateInput.value = startDateInput.value;
                }
            }

            validateDates();
        });
    }

    if (endDateInput) {
        endDateInput.addEventListener("change", validateDates);
    }

    if (bookingForm) {
        bookingForm.addEventListener("submit", function (event) {
            updateCalculation();

            if (!validateForm()) {
                event.preventDefault();
                event.stopPropagation();
                return;
            }

            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML =
                    '<i class="fas fa-spinner fa-spin"></i> Processing...';
            }
        });
    }

    autoHideAlerts();
    updateCalculation();
});