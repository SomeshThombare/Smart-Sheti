document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("searchInput");
    const statusFilter = document.getElementById("statusFilter");
    const categoryFilter = document.getElementById("categoryFilter");
    const resetFilters = document.getElementById("resetFilters");

    const rows = Array.from(document.querySelectorAll(".equipment-row"));
    const noResultRow = document.getElementById("noResultRow");
    const totalCount = document.getElementById("totalCount");

    const initialTotalCount = rows.length;

    function normalizeText(value) {
        return String(value || "").toLowerCase().trim();
    }

    function updateRowNumbers() {
        let number = 1;

        rows.forEach(function (row) {
            if (row.style.display !== "none") {
                const numberCell = row.querySelector(".row-number");

                if (numberCell) {
                    numberCell.textContent = number;
                }

                number++;
            }
        });
    }

    function updateTotalCount(count) {
        if (totalCount) {
            totalCount.textContent = count;
        }
    }

    function filterEquipment() {
        const searchValue = normalizeText(searchInput ? searchInput.value : "");
        const statusValue = normalizeText(statusFilter ? statusFilter.value : "");
        const categoryValue = normalizeText(categoryFilter ? categoryFilter.value : "");

        let visibleCount = 0;

        rows.forEach(function (row) {
            const rowSearch = normalizeText(row.dataset.search);
            const rowStatus = normalizeText(row.dataset.status);
            const rowCategory = normalizeText(row.dataset.category);

            const isSearchMatch = searchValue === "" || rowSearch.includes(searchValue);
            const isStatusMatch = statusValue === "" || rowStatus === statusValue;
            const isCategoryMatch = categoryValue === "" || rowCategory === categoryValue;

            if (isSearchMatch && isStatusMatch && isCategoryMatch) {
                row.style.display = "";
                visibleCount++;
            } else {
                row.style.display = "none";
            }
        });

        if (noResultRow) {
            noResultRow.classList.toggle("d-none", visibleCount > 0);
        }

        updateTotalCount(visibleCount);
        updateRowNumbers();
    }

    function resetAllFilters() {
        if (searchInput) {
            searchInput.value = "";
        }

        if (statusFilter) {
            statusFilter.value = "";
        }

        if (categoryFilter) {
            categoryFilter.value = "";
        }

        rows.forEach(function (row) {
            row.style.display = "";
            row.classList.remove("row-active");
        });

        if (noResultRow) {
            noResultRow.classList.add("d-none");
        }

        updateTotalCount(initialTotalCount);
        updateRowNumbers();
    }

    if (searchInput) {
        searchInput.addEventListener("input", filterEquipment);
    }

    if (statusFilter) {
        statusFilter.addEventListener("change", filterEquipment);
    }

    if (categoryFilter) {
        categoryFilter.addEventListener("change", filterEquipment);
    }

    if (resetFilters) {
        resetFilters.addEventListener("click", resetAllFilters);
    }

    rows.forEach(function (row) {
        row.addEventListener("click", function (event) {
            if (
                event.target.closest("a") ||
                event.target.closest("button") ||
                event.target.closest("form")
            ) {
                return;
            }

            rows.forEach(function (item) {
                item.classList.remove("row-active");
            });

            row.classList.add("row-active");
        });
    });

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

    const deleteForms = document.querySelectorAll(".custom-modal form");

    deleteForms.forEach(function (form) {
        form.addEventListener("submit", function () {
            const submitButton = form.querySelector("button[type='submit']");

            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
            }
        });
    });

    const deleteButtons = document.querySelectorAll(".action-btn.delete");

    deleteButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const icon = button.querySelector("i");

            if (icon) {
                icon.classList.add("fa-shake");

                setTimeout(function () {
                    icon.classList.remove("fa-shake");
                }, 600);
            }
        });
    });

    const actionLinks = document.querySelectorAll(".btn-dashboard, .btn-bookings, .btn-add, .empty-action-btn");

    actionLinks.forEach(function (link) {
        link.addEventListener("click", function () {
            link.classList.add("btn-loading");
        });
    });

    updateRowNumbers();
});