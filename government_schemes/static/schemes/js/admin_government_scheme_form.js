document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("schemeForm");
    const submitBtn = document.getElementById("submitBtn");

    const imageInput = document.getElementById("id_scheme_image");
    const imagePreview = document.getElementById("selectedImagePreview");

    const documentInput = document.getElementById("id_scheme_document");

    const messages = document.querySelectorAll(".message");

    // Auto hide success/error messages
    messages.forEach(function (message) {
        setTimeout(function () {
            message.style.transition = "all 0.5s ease";
            message.style.opacity = "0";
            message.style.transform = "translateY(-10px)";

            setTimeout(function () {
                message.remove();
            }, 500);
        }, 4000);
    });

    // Image preview + validation
    if (imageInput && imagePreview) {
        imageInput.addEventListener("change", function () {
            const file = this.files[0];

            imagePreview.classList.add("hidden");
            imagePreview.src = "";

            if (!file) {
                return;
            }

            const allowedImageTypes = [
                "image/jpeg",
                "image/jpg",
                "image/png",
                "image/webp"
            ];

            const maxImageSize = 2 * 1024 * 1024;

            if (!allowedImageTypes.includes(file.type)) {
                alert("Only JPG, JPEG, PNG and WEBP image files are allowed.");
                this.value = "";
                return;
            }

            if (file.size > maxImageSize) {
                alert("Image size must be less than 2 MB.");
                this.value = "";
                return;
            }

            const reader = new FileReader();

            reader.onload = function (event) {
                imagePreview.src = event.target.result;
                imagePreview.classList.remove("hidden");
            };

            reader.readAsDataURL(file);
        });
    }

    // Document validation
    if (documentInput) {
        documentInput.addEventListener("change", function () {
            const file = this.files[0];

            if (!file) {
                return;
            }

            const allowedDocumentTypes = [
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ];

            const allowedExtensions = [".pdf", ".doc", ".docx"];
            const fileName = file.name.toLowerCase();

            const hasValidExtension = allowedExtensions.some(function (extension) {
                return fileName.endsWith(extension);
            });

            const maxDocumentSize = 5 * 1024 * 1024;

            if (!allowedDocumentTypes.includes(file.type) && !hasValidExtension) {
                alert("Only PDF, DOC and DOCX files are allowed.");
                this.value = "";
                return;
            }

            if (file.size > maxDocumentSize) {
                alert("Document size must be less than 5 MB.");
                this.value = "";
            }
        });
    }

    // Required field basic validation
    function validateRequiredFields() {
        const requiredInputs = form.querySelectorAll(
            "input[required], select[required], textarea[required]"
        );

        let isValid = true;

        requiredInputs.forEach(function (input) {
            input.classList.remove("field-error");

            if (!input.value.trim()) {
                input.classList.add("field-error");
                isValid = false;
            }
        });

        return isValid;
    }

    // URL validation
    function isValidUrl(value) {
        if (!value) {
            return true;
        }

        try {
            new URL(value);
            return true;
        } catch (error) {
            return false;
        }
    }

    function validateUrlFields() {
        const officialLink = document.getElementById("id_official_link");
        const applyLink = document.getElementById("id_apply_link");

        let isValid = true;

        [officialLink, applyLink].forEach(function (input) {
            if (!input) return;

            input.classList.remove("field-error");

            if (input.value.trim() && !isValidUrl(input.value.trim())) {
                input.classList.add("field-error");
                isValid = false;
            }
        });

        return isValid;
    }

    // Submit loading state
    if (form && submitBtn) {
        form.addEventListener("submit", function (event) {
            const requiredValid = validateRequiredFields();
            const urlsValid = validateUrlFields();

            if (!requiredValid) {
                event.preventDefault();
                alert("Please fill all required fields.");
                return;
            }

            if (!urlsValid) {
                event.preventDefault();
                alert("Please enter valid URLs. Example: https://pmkisan.gov.in/");
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML =
                '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';
        });
    }

    // Remove error style on input
    const allInputs = document.querySelectorAll("input, select, textarea");

    allInputs.forEach(function (input) {
        input.addEventListener("input", function () {
            input.classList.remove("field-error");
        });

        input.addEventListener("change", function () {
            input.classList.remove("field-error");
        });
    });
});