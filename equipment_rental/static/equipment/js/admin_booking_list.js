document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("searchInput");
    const bookingStatusFilter = document.getElementById("bookingStatusFilter");
    const paymentStatusFilter = document.getElementById("paymentStatusFilter");
    const resetButton = document.getElementById("resetFilters");

    const bookingRows = Array.from(document.querySelectorAll(".booking-row"));
    const noResultRow = document.getElementById("noResultRow");
    const alerts = document.querySelectorAll(".alert");

    function normalize(value) {
        return String(value || "").toLowerCase().trim();
    }

    function updateRowNumbers() {
        let serialNumber = 1;

        bookingRows.forEach(function (row) {
            if (row.classList.contains("d-none")) {
                return;
            }

            const numberCell = row.querySelector(".row-number");

            if (numberCell) {
                numberCell.textContent = serialNumber;
                serialNumber++;
            }
        });
    }

    function applyFilters() {
        const searchValue = normalize(searchInput ? searchInput.value : "");
        const bookingStatusValue = normalize(
            bookingStatusFilter ? bookingStatusFilter.value : ""
        );
        const paymentStatusValue = normalize(
            paymentStatusFilter ? paymentStatusFilter.value : ""
        );

        let visibleCount = 0;

        bookingRows.forEach(function (row) {
            const rowSearch = normalize(row.dataset.search);
            const rowBookingStatus = normalize(row.dataset.bookingStatus);
            const rowPaymentStatus = normalize(row.dataset.paymentStatus);

            const matchesSearch =
                searchValue === "" || rowSearch.includes(searchValue);

            const matchesBookingStatus =
                bookingStatusValue === "" || rowBookingStatus === bookingStatusValue;

            const matchesPaymentStatus =
                paymentStatusValue === "" || rowPaymentStatus === paymentStatusValue;

            if (matchesSearch && matchesBookingStatus && matchesPaymentStatus) {
                row.classList.remove("d-none");
                visibleCount++;
            } else {
                row.classList.add("d-none");
            }
        });

        if (noResultRow) {
            if (visibleCount === 0 && bookingRows.length > 0) {
                noResultRow.classList.remove("d-none");
            } else {
                noResultRow.classList.add("d-none");
            }
        }

        updateRowNumbers();
    }

    function resetFilters() {
        if (searchInput) {
            searchInput.value = "";
        }

        if (bookingStatusFilter) {
            bookingStatusFilter.value = "";
        }

        if (paymentStatusFilter) {
            paymentStatusFilter.value = "";
        }

        applyFilters();
    }

    function autoHideAlerts() {
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

    function addTableHoverEffect() {
        bookingRows.forEach(function (row) {
            row.addEventListener("mouseenter", function () {
                row.style.backgroundColor = "#f8fff8";
            });

            row.addEventListener("mouseleave", function () {
                row.style.backgroundColor = "";
            });
        });
    }

    function addButtonClickEffect() {
        const buttons = document.querySelectorAll(
            ".btn-header, .btn-reset-full, .action-btn, .empty-action"
        );

        buttons.forEach(function (button) {
            button.addEventListener("click", function () {
                button.style.transform = "scale(0.96)";

                setTimeout(function () {
                    button.style.transform = "";
                }, 150);
            });
        });
    }

    if (searchInput) {
        searchInput.addEventListener("input", applyFilters);
    }

    if (bookingStatusFilter) {
        bookingStatusFilter.addEventListener("change", applyFilters);
    }

    if (paymentStatusFilter) {
        paymentStatusFilter.addEventListener("change", applyFilters);
    }

    if (resetButton) {
        resetButton.addEventListener("click", resetFilters);
    }

    autoHideAlerts();
    addTableHoverEffect();
    addButtonClickEffect();
    applyFilters();
});