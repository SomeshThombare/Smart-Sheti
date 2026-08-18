document.addEventListener("DOMContentLoaded", function () {
    const mainImage = document.getElementById("mainImage");
    const modal = document.getElementById("imagePreviewModal");
    const closeBtn = document.getElementById("closePreview");
    const previewImage = document.getElementById("previewImage");

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
            }, 3000);
        });
    }

    function openImagePreview() {
        if (!modal) {
            return;
        }

        if (mainImage && previewImage) {
            previewImage.src = mainImage.src;
            previewImage.alt = mainImage.alt || "Equipment Image";
        }

        modal.style.display = "flex";
        document.body.style.overflow = "hidden";
    }

    function closeImagePreview() {
        if (!modal) {
            return;
        }

        modal.style.display = "none";
        document.body.style.overflow = "";
    }

    if (mainImage) {
        mainImage.addEventListener("click", openImagePreview);
    }

    if (closeBtn) {
        closeBtn.addEventListener("click", closeImagePreview);
    }

    if (modal) {
        modal.addEventListener("click", function (event) {
            if (event.target === modal) {
                closeImagePreview();
            }
        });
    }

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeImagePreview();
        }
    });

    autoHideAlerts();
});