document.addEventListener("DOMContentLoaded", function () {
    const cancelForms = document.querySelectorAll(".cancel-form");
    const actionButtons = document.querySelectorAll(
        ".btn-secondary-custom, .btn-equipment, .btn-pay, .btn-cancel-booking, .btn-back"
    );

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
            }, 3500);
        });
    }

    cancelForms.forEach(function (form) {
        form.addEventListener("submit", function (event) {
            const confirmed = confirm("Are you sure you want to cancel this booking?");

            if (!confirmed) {
                event.preventDefault();
                return;
            }

            const button = form.querySelector(".btn-cancel-booking");

            if (button) {
                button.disabled = true;
                button.innerHTML =
                    '<i class="fas fa-spinner fa-spin"></i> Cancelling...';
            }
        });
    });

    actionButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            button.classList.add("clicked");

            setTimeout(function () {
                button.classList.remove("clicked");
            }, 200);
        });
    });

    autoHideAlerts();
});