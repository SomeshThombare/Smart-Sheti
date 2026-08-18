document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");
    const submitButton = document.querySelector(".btn-submit");
    const imageInput = document.querySelector('input[type="file"]');
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

    function showError(input, message) {
        clearError(input);

        input.classList.add("is-invalid");

        const errorBox = document.createElement("div");
        errorBox.className = "invalid-feedback custom-error";
        errorBox.textContent = message;

        input.parentElement.appendChild(errorBox);
    }

    function clearError(input) {
        if (!input) {
            return;
        }

        input.classList.remove("is-invalid");

        const oldError = input.parentElement.querySelector(".custom-error");

        if (oldError) {
            oldError.remove();
        }
    }

    function validateImage() {
        if (!imageInput || !imageInput.files.length) {
            return true;
        }

        const file = imageInput.files[0];

        const allowedTypes = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/webp"
        ];

        const maxSize = 5 * 1024 * 1024;

        if (!allowedTypes.includes(file.type)) {
            showError(imageInput, "Only JPG, JPEG, PNG and WEBP images are allowed.");
            imageInput.value = "";
            removeLivePreview();
            return false;
        }

        if (file.size > maxSize) {
            showError(imageInput, "Image size must be less than 5MB.");
            imageInput.value = "";
            removeLivePreview();
            return false;
        }

        clearError(imageInput);
        showLivePreview(file);
        return true;
    }

    function removeLivePreview() {
        const oldPreview = document.querySelector(".live-preview");

        if (oldPreview) {
            oldPreview.remove();
        }
    }

    function showLivePreview(file) {
        removeLivePreview();

        const reader = new FileReader();

        reader.onload = function (event) {
            const previewBox = document.createElement("div");
            previewBox.className = "image-preview live-preview mt-3";

            const image = document.createElement("img");
            image.src = event.target.result;
            image.alt = "Selected Equipment Image";

            previewBox.appendChild(image);
            imageInput.parentElement.appendChild(previewBox);
        };

        reader.readAsDataURL(file);
    }

    function validateRequiredFields() {
        let isValid = true;

        const requiredFields = form.querySelectorAll(
            "input[required], select[required], textarea[required]"
        );

        requiredFields.forEach(function (field) {
            clearError(field);

            if (!String(field.value || "").trim()) {
                showError(field, "This field is required.");
                isValid = false;
            }
        });

        return isValid;
    }

    function validateRentalPrice() {
        const priceInput = document.querySelector('[name="rental_price_per_day"]');

        if (!priceInput) {
            return true;
        }

        clearError(priceInput);

        const price = parseFloat(priceInput.value);

        if (isNaN(price) || price <= 0) {
            showError(priceInput, "Rental price must be greater than 0.");
            return false;
        }

        return true;
    }

    function validateForm() {
        const requiredValid = validateRequiredFields();
        const priceValid = validateRentalPrice();
        const imageValid = validateImage();

        return requiredValid && priceValid && imageValid;
    }

    if (imageInput) {
        imageInput.addEventListener("change", validateImage);
    }

    if (form) {
        form.addEventListener("submit", function (event) {
            if (!validateForm()) {
                event.preventDefault();
                event.stopPropagation();
                return;
            }

            if (submitButton) {
                submitButton.disabled = true;
                submitButton.classList.add("loading");
                submitButton.innerHTML =
                    '<i class="fas fa-spinner fa-spin"></i> Saving...';
            }
        });
    }

    autoHideAlerts();
});