document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("searchInput");
    const bookingStatusFilter = document.getElementById("bookingStatusFilter");
    const paymentStatusFilter = document.getElementById("paymentStatusFilter");
    const resetButton = document.getElementById("resetFilters");

    const bookingItems = Array.from(document.querySelectorAll(".booking-item"));
    const emptySearchResult = document.getElementById("emptySearchResult");
    const totalCount = document.getElementById("totalCount");

    function normalize(value) {
        return String(value || "").toLowerCase().trim();
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

        bookingItems.forEach(function (item) {
            const itemSearch = normalize(item.dataset.search);
            const itemBookingStatus = normalize(item.dataset.bookingStatus);
            const itemPaymentStatus = normalize(item.dataset.paymentStatus);

            const matchesSearch =
                searchValue === "" || itemSearch.includes(searchValue);

            const matchesBookingStatus =
                bookingStatusValue === "" || itemBookingStatus === bookingStatusValue;

            const matchesPaymentStatus =
                paymentStatusValue === "" || itemPaymentStatus === paymentStatusValue;

            if (matchesSearch && matchesBookingStatus && matchesPaymentStatus) {
                item.classList.remove("d-none");
                visibleCount++;
            } else {
                item.classList.add("d-none");
            }
        });

        if (totalCount) {
            totalCount.textContent = visibleCount;
        }

        if (emptySearchResult) {
            if (visibleCount === 0 && bookingItems.length > 0) {
                emptySearchResult.classList.remove("d-none");
            } else {
                emptySearchResult.classList.add("d-none");
            }
        }
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
    applyFilters();
});