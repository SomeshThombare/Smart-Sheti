document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("searchInput");
    const categoryFilter = document.getElementById("categoryFilter");
    const statusFilter = document.getElementById("statusFilter");
    const resetButton = document.getElementById("resetFilters");

    const items = Array.from(document.querySelectorAll(".equipment-item"));
    const emptySearchResult = document.getElementById("emptySearchResult");
    const totalCount = document.getElementById("totalCount");

    function normalize(value) {
        return String(value || "").toLowerCase().trim();
    }

    function updateTotalCount(count) {
        if (totalCount) {
            totalCount.textContent = count;
        }
    }

    function toggleEmptyResult(count) {
        if (!emptySearchResult) {
            return;
        }

        if (count === 0 && items.length > 0) {
            emptySearchResult.classList.remove("d-none");
        } else {
            emptySearchResult.classList.add("d-none");
        }
    }

    function applyFilters() {
        const searchValue = normalize(searchInput ? searchInput.value : "");
        const categoryValue = normalize(categoryFilter ? categoryFilter.value : "");
        const statusValue = normalize(statusFilter ? statusFilter.value : "");

        let visibleCount = 0;

        items.forEach(function (item) {
            const itemSearch = normalize(item.dataset.search);
            const itemCategory = normalize(item.dataset.category);
            const itemStatus = normalize(item.dataset.status);

            const matchesSearch =
                searchValue === "" || itemSearch.includes(searchValue);

            const matchesCategory =
                categoryValue === "" || itemCategory === categoryValue;

            const matchesStatus =
                statusValue === "" || itemStatus === statusValue;

            if (matchesSearch && matchesCategory && matchesStatus) {
                item.classList.remove("d-none");
                visibleCount++;
            } else {
                item.classList.add("d-none");
            }
        });

        updateTotalCount(visibleCount);
        toggleEmptyResult(visibleCount);
    }

    function resetFilters() {
        if (searchInput) {
            searchInput.value = "";
        }

        if (categoryFilter) {
            categoryFilter.value = "";
        }

        if (statusFilter) {
            statusFilter.value = "";
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

    if (categoryFilter) {
        categoryFilter.addEventListener("change", applyFilters);
    }

    if (statusFilter) {
        statusFilter.addEventListener("change", applyFilters);
    }

    if (resetButton) {
        resetButton.addEventListener("click", resetFilters);
    }

    autoHideAlerts();
    applyFilters();
});