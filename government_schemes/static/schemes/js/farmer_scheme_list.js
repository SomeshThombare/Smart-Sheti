document.addEventListener("DOMContentLoaded", function () {
    const successMessage = document.getElementById("successMessage");
    const errorMessage = document.getElementById("errorMessage");

    const searchInput = document.getElementById("searchInput");
    const categoryFilter = document.getElementById("categoryFilter");
    const stateFilter = document.getElementById("stateFilter");
    const statusFilter = document.getElementById("statusFilter");

    const clearFilters = document.getElementById("clearFilters");
    const clearFiltersEmpty = document.getElementById("clearFiltersEmpty");

    const schemeItems = Array.from(document.querySelectorAll(".scheme-item"));
    const noSearchResult = document.getElementById("noSearchResult");

    function autoHideMessage(messageElement) {
        if (!messageElement) return;

        setTimeout(function () {
            messageElement.classList.add("hide-message");

            setTimeout(function () {
                messageElement.style.display = "none";
            }, 500);
        }, 5000);
    }

    autoHideMessage(successMessage);
    autoHideMessage(errorMessage);

    function removeDuplicateOptions(selectElement) {
        if (!selectElement) return;

        const seenValues = new Set();

        Array.from(selectElement.options).forEach(function (option) {
            const value = option.value.trim().toLowerCase();

            if (value === "") return;

            if (seenValues.has(value)) {
                option.remove();
            } else {
                seenValues.add(value);
            }
        });
    }

    removeDuplicateOptions(categoryFilter);
    removeDuplicateOptions(stateFilter);

    function normalize(value) {
        return String(value || "").toLowerCase().trim();
    }

    function filterSchemes() {
        const searchValue = normalize(searchInput ? searchInput.value : "");
        const categoryValue = normalize(categoryFilter ? categoryFilter.value : "");
        const stateValue = normalize(stateFilter ? stateFilter.value : "");
        const statusValue = normalize(statusFilter ? statusFilter.value : "");

        let visibleCount = 0;

        schemeItems.forEach(function (item) {
            const searchText = normalize(item.dataset.search);
            const category = normalize(item.dataset.category);
            const state = normalize(item.dataset.state);
            const status = normalize(item.dataset.status);
            const featured = normalize(item.dataset.featured);

            const matchSearch = searchValue === "" || searchText.includes(searchValue);
            const matchCategory = categoryValue === "" || category === categoryValue;
            const matchState = stateValue === "" || state === stateValue;

            let matchStatus = true;

            if (statusValue === "featured") {
                matchStatus = featured === "featured";
            } else if (statusValue !== "") {
                matchStatus = status === statusValue;
            }

            if (matchSearch && matchCategory && matchState && matchStatus) {
                item.style.display = "";
                visibleCount++;
            } else {
                item.style.display = "none";
            }
        });

        if (noSearchResult) {
            noSearchResult.style.display = visibleCount === 0 ? "block" : "none";
        }
    }

    function resetFilters() {
        if (searchInput) searchInput.value = "";
        if (categoryFilter) categoryFilter.value = "";
        if (stateFilter) stateFilter.value = "";
        if (statusFilter) statusFilter.value = "";

        filterSchemes();
    }

    [searchInput, categoryFilter, stateFilter, statusFilter].forEach(function (element) {
        if (!element) return;

        element.addEventListener("input", filterSchemes);
        element.addEventListener("change", filterSchemes);
    });

    if (clearFilters) {
        clearFilters.addEventListener("click", resetFilters);
    }

    if (clearFiltersEmpty) {
        clearFiltersEmpty.addEventListener("click", resetFilters);
    }

    document.querySelectorAll(".save-btn").forEach(function (button) {
        button.addEventListener("click", function () {
            button.classList.toggle("saved");

            const icon = button.querySelector("i");

            if (!icon) return;

            if (button.classList.contains("saved")) {
                icon.classList.remove("fa-regular");
                icon.classList.add("fa-solid");
            } else {
                icon.classList.remove("fa-solid");
                icon.classList.add("fa-regular");
            }
        });
    });

    document.querySelectorAll(".btn-share").forEach(function (button) {
        button.addEventListener("click", function () {
            const title = button.getAttribute("data-title") || "Government Scheme";
            const relativeUrl = button.getAttribute("data-url") || "";
            const url = window.location.origin + relativeUrl;

            if (navigator.share) {
                navigator.share({
                    title: title,
                    text: "Check this government scheme on Smart Sheti",
                    url: url
                }).catch(function () {
                    // User cancelled share dialog
                });

                return;
            }

            if (navigator.clipboard) {
                navigator.clipboard.writeText(url).then(function () {
                    const oldHTML = button.innerHTML;

                    button.innerHTML = '<i class="fa-solid fa-check"></i> Link Copied';

                    setTimeout(function () {
                        button.innerHTML = oldHTML;
                    }, 2000);
                });
            }
        });
    });

    filterSchemes();
});