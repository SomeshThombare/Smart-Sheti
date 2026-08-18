document.addEventListener("DOMContentLoaded", function () {
    setupTableSearch();
    animateStatCards();
});

function setupTableSearch() {
    const searchInput = document.getElementById("chatSearch");
    const table = document.getElementById("recentChatsTable");

    if (!searchInput || !table) {
        return;
    }

    searchInput.addEventListener("input", function () {
        const searchValue = searchInput.value.toLowerCase().trim();
        const rows = table.querySelectorAll("tbody tr");

        rows.forEach(function (row) {
            const rowText = row.textContent.toLowerCase();

            if (rowText.includes(searchValue)) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    });
}

function animateStatCards() {
    const cards = document.querySelectorAll(".stat-card");

    cards.forEach(function (card, index) {
        card.style.opacity = "0";
        card.style.transform = "translateY(15px)";

        setTimeout(function () {
            card.style.transition = "0.35s ease";
            card.style.opacity = "1";
            card.style.transform = "translateY(0)";
        }, index * 80);
    });
}