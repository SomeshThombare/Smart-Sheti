document.addEventListener("DOMContentLoaded", function () {

    // ==========================
    // ELEMENTS
    // ==========================

    const searchInput = document.getElementById("searchInput");
    const bookingStatusFilter = document.getElementById("bookingStatusFilter");
    const paymentStatusFilter = document.getElementById("paymentStatusFilter");
    const resetFilters = document.getElementById("resetFilters");

    const bookingRows = document.querySelectorAll(".booking-row");

    const historyCount = document.getElementById("historyCount");

    const emptyRow = document.getElementById("emptyRow");

    // ==========================
    // AUTO HIDE ALERT
    // ==========================

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

    // ==========================
    // FILTER FUNCTION
    // ==========================

    function applyFilters() {

        const searchValue =
            searchInput ?
            searchInput.value.toLowerCase().trim() :
            "";

        const bookingStatus =
            bookingStatusFilter ?
            bookingStatusFilter.value.toLowerCase().trim() :
            "";

        const paymentStatus =
            paymentStatusFilter ?
            paymentStatusFilter.value.toLowerCase().trim() :
            "";

        let visibleCount = 0;

        bookingRows.forEach(function (row) {

            const searchData =
                (row.dataset.search || "").toLowerCase();

            const bookingData =
                (row.dataset.bookingStatus || "").toLowerCase();

            const paymentData =
                (row.dataset.paymentStatus || "").toLowerCase();

            const matchSearch =
                !searchValue ||
                searchData.includes(searchValue);

            const matchBooking =
                !bookingStatus ||
                bookingData === bookingStatus;

            const matchPayment =
                !paymentStatus ||
                paymentData === paymentStatus;

            if (
                matchSearch &&
                matchBooking &&
                matchPayment
            ) {

                row.style.display = "";

                visibleCount++;

            } else {

                row.style.display = "none";

            }

        });

        // Update Counter

        if (historyCount) {

            historyCount.textContent = visibleCount;

        }

        // Empty Message

        if (emptyRow) {

            if (
                visibleCount === 0 &&
                bookingRows.length > 0
            ) {

                emptyRow.style.display = "";

            } else {

                emptyRow.style.display = "none";

            }

        }

    }

    // ==========================
    // EVENTS
    // ==========================

    if (searchInput) {

        searchInput.addEventListener(
            "keyup",
            applyFilters
        );

    }

    if (bookingStatusFilter) {

        bookingStatusFilter.addEventListener(
            "change",
            applyFilters
        );

    }

    if (paymentStatusFilter) {

        paymentStatusFilter.addEventListener(
            "change",
            applyFilters
        );

    }

    // ==========================
    // RESET FILTERS
    // ==========================

    if (resetFilters) {

        resetFilters.addEventListener(
            "click",
            function () {

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
        );

    }

    // ==========================
    // TABLE ROW HOVER EFFECT
    // ==========================

    bookingRows.forEach(function (row) {

        row.addEventListener("mouseenter", function () {

            row.style.transition =
                "all 0.3s ease";

            row.style.backgroundColor =
                "#f8fff8";

        });

        row.addEventListener("mouseleave", function () {

            row.style.backgroundColor =
                "";

        });

    });

    // ==========================
    // INITIAL LOAD
    // ==========================

    applyFilters();

});