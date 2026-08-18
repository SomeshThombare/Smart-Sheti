document.addEventListener("DOMContentLoaded", function () {
    const menuToggle = document.getElementById("menuToggle");
    const sidebar = document.getElementById("sidebar");
    const sidebarOverlay = document.getElementById("sidebarOverlay");
    const mainContent = document.getElementById("mainContent");

    const searchInput = document.getElementById("searchInput");
    const statusFilter = document.getElementById("statusFilter");
    const featuredFilter = document.getElementById("featuredFilter");
    const resetFiltersBtn = document.getElementById("resetFilters");
    const clearFiltersBtn = document.getElementById("clearFilters");

    const tableWrap = document.getElementById("tableWrap");
    const searchEmptyBox = document.getElementById("searchEmptyBox");
    const schemeCount = document.getElementById("schemeCount");

    function getRows() {
        return Array.from(document.querySelectorAll("#schemeTable tbody tr"));
    }

    function getCSRFToken() {
        let cookieValue = null;
        const cookies = document.cookie ? document.cookie.split(";") : [];

        for (let cookie of cookies) {
            cookie = cookie.trim();

            if (cookie.startsWith("csrftoken=")) {
                cookieValue = decodeURIComponent(
                    cookie.substring("csrftoken=".length)
                );
                break;
            }
        }

        return cookieValue;
    }

    function autoHideElement(element) {
        if (!element) return;

        setTimeout(function () {
            element.style.transition = "all 0.5s ease";
            element.style.opacity = "0";
            element.style.transform = "translateY(-10px)";

            setTimeout(function () {
                element.classList.add("hidden");
                element.style.opacity = "";
                element.style.transform = "";
            }, 500);
        }, 4000);
    }

    function showMessage(boxId, iconClass, message) {
        const box = document.getElementById(boxId);

        if (!box) return;

        box.innerHTML = "";

        const icon = document.createElement("i");
        icon.className = iconClass;

        box.appendChild(icon);
        box.appendChild(document.createTextNode(" " + message));

        box.classList.remove("hidden");
        box.style.opacity = "1";

        box.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

        autoHideElement(box);
    }

    function showSuccess(message) {
        const errorBox = document.getElementById("jsErrorBox");

        if (errorBox) {
            errorBox.classList.add("hidden");
        }

        showMessage(
            "jsSuccessBox",
            "fa-solid fa-circle-check",
            message || "Action completed successfully."
        );
    }

    function showError(message) {
        const successBox = document.getElementById("jsSuccessBox");

        if (successBox) {
            successBox.classList.add("hidden");
        }

        showMessage(
            "jsErrorBox",
            "fa-solid fa-circle-exclamation",
            message || "Something went wrong."
        );
    }

    function updateStats() {
        const rows = getRows();

        const visibleRows = rows.filter(function (row) {
            return row.style.display !== "none";
        });

        if (schemeCount) {
            schemeCount.textContent = visibleRows.length;
        }

        visibleRows.forEach(function (row, index) {
            const numberCell = row.querySelector(".row-number");

            if (numberCell) {
                numberCell.textContent = index + 1;
            }
        });

        return rows.length;
    }

    function applyFilters() {
        const searchValue = searchInput
            ? searchInput.value.toLowerCase().trim()
            : "";

        const statusValue = statusFilter
            ? statusFilter.value.toLowerCase().trim()
            : "";

        const featuredValue = featuredFilter
            ? featuredFilter.value.toLowerCase().trim()
            : "";

        let visibleCount = 0;

        getRows().forEach(function (row) {
            const rowText = row.textContent.toLowerCase();
            const rowStatus = (row.dataset.status || "").toLowerCase();
            const rowFeatured = (row.dataset.featured || "").toLowerCase();

            const textMatched = !searchValue || rowText.includes(searchValue);
            const statusMatched = !statusValue || rowStatus === statusValue;
            const featuredMatched = !featuredValue || rowFeatured === featuredValue;

            const matched = textMatched && statusMatched && featuredMatched;

            row.style.display = matched ? "" : "none";

            if (matched) {
                visibleCount++;
            }
        });

        if (tableWrap && searchEmptyBox) {
            if (visibleCount === 0) {
                tableWrap.classList.add("hidden");
                searchEmptyBox.classList.remove("hidden");
            } else {
                tableWrap.classList.remove("hidden");
                searchEmptyBox.classList.add("hidden");
            }
        }

        updateStats();
    }

    function resetFilters() {
        if (searchInput) searchInput.value = "";
        if (statusFilter) statusFilter.value = "";
        if (featuredFilter) featuredFilter.value = "";

        applyFilters();
    }

    async function deleteScheme(button) {
        const deleteUrl = button.getAttribute("data-delete-url");

        if (!deleteUrl) {
            showError("Delete URL not found.");
            return;
        }

        const confirmed = confirm(
            "Are you sure you want to delete this government scheme?"
        );

        if (!confirmed) return;

        button.disabled = true;

        const oldHTML = button.innerHTML;
        button.innerHTML =
            '<i class="fa-solid fa-spinner fa-spin"></i> Deleting...';

        try {
            const response = await fetch(deleteUrl, {
                method: "DELETE",
                headers: {
                    "X-CSRFToken": getCSRFToken(),
                    "Accept": "application/json",
                    "X-Requested-With": "XMLHttpRequest"
                }
            });

            let data = {};
            const contentType = response.headers.get("content-type") || "";

            if (contentType.includes("application/json")) {
                data = await response.json();
            }

            if (!response.ok) {
                throw new Error(
                    data.message || "Delete failed. Please try again."
                );
            }

            const row = button.closest("tr");

            if (row) {
                row.style.transition = "all 0.4s ease";
                row.style.opacity = "0";
                row.style.transform = "translateX(20px)";

                setTimeout(function () {
                    row.remove();

                    showSuccess(
                        data.message ||
                        "Government scheme deleted successfully."
                    );

                    const remainingRows = updateStats();
                    applyFilters();

                    if (remainingRows === 0) {
                        setTimeout(function () {
                            window.location.reload();
                        }, 800);
                    }
                }, 400);
            }

        } catch (error) {
            showError(error.message || "Delete failed. Please try again.");

            button.disabled = false;
            button.innerHTML = oldHTML;
        }
    }

    if (menuToggle && sidebar) {
        menuToggle.addEventListener("click", function () {
            if (window.innerWidth <= 900) {
                sidebar.classList.toggle("active");

                if (sidebarOverlay) {
                    sidebarOverlay.classList.toggle("active");
                }
            } else {
                sidebar.classList.toggle("hidden-desktop");

                if (mainContent) {
                    mainContent.classList.toggle("full-width");
                }
            }
        });
    }

    if (sidebarOverlay && sidebar) {
        sidebarOverlay.addEventListener("click", function () {
            sidebar.classList.remove("active");
            sidebarOverlay.classList.remove("active");
        });
    }

    if (searchInput) {
        searchInput.addEventListener("input", applyFilters);
    }

    if (statusFilter) {
        statusFilter.addEventListener("change", applyFilters);
    }

    if (featuredFilter) {
        featuredFilter.addEventListener("change", applyFilters);
    }

    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener("click", resetFilters);
    }

    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener("click", resetFilters);
    }

    document.querySelectorAll(".delete-btn").forEach(function (button) {
        button.addEventListener("click", function () {
            deleteScheme(button);
        });
    });

    getRows().forEach(function (row) {
        row.addEventListener("click", function (event) {
            if (
                event.target.closest("a") ||
                event.target.closest("button")
            ) {
                return;
            }

            getRows().forEach(function (item) {
                item.classList.remove("row-active");
            });

            row.classList.add("row-active");
        });
    });

    autoHideElement(document.getElementById("autoMessage"));
    autoHideElement(document.getElementById("autoErrorMessage"));

    updateStats();
});