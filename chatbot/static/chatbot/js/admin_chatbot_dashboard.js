document.addEventListener("DOMContentLoaded", function () {
    calculateRates();
    setupChatSearch();
});

function getPercentage(value, total) {
    value = Number(value || 0);
    total = Number(total || 0);

    if (total <= 0) {
        return "0%";
    }

    return ((value / total) * 100).toFixed(1) + "%";
}

function calculateRates() {
    const successRate = document.getElementById("successRate");
    const failedRate = document.getElementById("failedRate");
    const imageRate = document.getElementById("imageRate");
    const pdfRate = document.getElementById("pdfRate");

    if (successRate) {
        successRate.textContent = getPercentage(
            successRate.dataset.success,
            successRate.dataset.total
        );
    }

    if (failedRate) {
        failedRate.textContent = getPercentage(
            failedRate.dataset.failed,
            failedRate.dataset.total
        );
    }

    if (imageRate) {
        imageRate.textContent = getPercentage(
            imageRate.dataset.image,
            imageRate.dataset.total
        );
    }

    if (pdfRate) {
        pdfRate.textContent = getPercentage(
            pdfRate.dataset.pdf,
            pdfRate.dataset.total
        );
    }
}

function setupChatSearch() {
    const searchInput = document.getElementById("chatSearch");
    const table = document.getElementById("recentChatsTable");

    if (!searchInput || !table) {
        return;
    }

    searchInput.addEventListener("input", function () {
        const filter = searchInput.value.toLowerCase().trim();
        const rows = table.querySelectorAll("tbody tr");

        rows.forEach(function (row) {
            const rowText = row.textContent.toLowerCase();

            if (rowText.includes(filter)) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    });
}