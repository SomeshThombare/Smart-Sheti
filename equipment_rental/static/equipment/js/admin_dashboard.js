document.addEventListener("DOMContentLoaded", function () {
    const alerts = document.querySelectorAll(".alert");
    const statCards = document.querySelectorAll(".stat-card");
    const actionCards = document.querySelectorAll(".action-card");
    const recentSection = document.querySelector(".recent-section");
    const tableRows = document.querySelectorAll(".dashboard-table tbody tr");
    const counters = document.querySelectorAll(".stat-card h3");

    function autoHideAlerts() {
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

    function animateCards() {
        const cards = Array.from(statCards).concat(Array.from(actionCards));

        if (recentSection) {
            cards.push(recentSection);
        }

        cards.forEach(function (card, index) {
            card.style.opacity = "0";
            card.style.transform = "translateY(20px)";
            card.style.transition = "all 0.5s ease";

            setTimeout(function () {
                card.style.opacity = "1";
                card.style.transform = "translateY(0)";
            }, index * 100);
        });
    }

    function animateCounters() {
        counters.forEach(function (counter) {
            const target = parseInt(counter.textContent, 10) || 0;
            let count = 0;
            const increment = Math.max(1, Math.ceil(target / 40));

            counter.textContent = "0";

            function updateCounter() {
                count += increment;

                if (count >= target) {
                    counter.textContent = target;
                    return;
                }

                counter.textContent = count;
                requestAnimationFrame(updateCounter);
            }

            updateCounter();
        });
    }

    function addCardHoverEffect() {
        const cards = Array.from(statCards).concat(Array.from(actionCards));

        cards.forEach(function (card) {
            card.addEventListener("mouseenter", function () {
                card.style.transform = "translateY(-5px)";
                card.style.boxShadow = "0 18px 45px rgba(0, 0, 0, 0.12)";
            });

            card.addEventListener("mouseleave", function () {
                card.style.transform = "translateY(0)";
                card.style.boxShadow = "";
            });
        });
    }

    function addTableHoverEffect() {
        tableRows.forEach(function (row) {
            row.addEventListener("mouseenter", function () {
                row.style.backgroundColor = "#f8fff8";
                row.style.transition = "0.3s ease";
            });

            row.addEventListener("mouseleave", function () {
                row.style.backgroundColor = "";
            });
        });
    }

    function addButtonClickEffect() {
        const buttons = document.querySelectorAll(
            ".btn-main, .btn-light-action, .btn-view, .section-header a"
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

    autoHideAlerts();
    animateCards();
    animateCounters();
    addCardHoverEffect();
    addTableHoverEffect();
    addButtonClickEffect();
});