document.addEventListener("DOMContentLoaded", function () {

    /*
    ==========================================
    AUTO HIDE ALERTS
    ==========================================
    */

    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {

        setTimeout(function () {

            alert.style.transition =
                "opacity 0.5s ease, transform 0.5s ease";

            alert.style.opacity = "0";
            alert.style.transform = "translateY(-10px)";

            setTimeout(function () {
                alert.remove();
            }, 500);

        }, 3000);

    });


    /*
    ==========================================
    COUNTER ANIMATION
    ==========================================
    */

    const counters = document.querySelectorAll(".stat-card h3");

    counters.forEach(function (counter) {

        const target = parseInt(counter.innerText) || 0;

        let count = 0;

        const duration = 1200;

        const increment = Math.max(
            Math.ceil(target / 60),
            1
        );

        const timer = setInterval(function () {

            count += increment;

            if (count >= target) {

                counter.innerText = target;
                clearInterval(timer);

            } else {

                counter.innerText = count;

            }

        }, duration / 60);

    });


    /*
    ==========================================
    CARD HOVER EFFECT
    ==========================================
    */

    const cards = document.querySelectorAll(
        ".stat-card, .action-card"
    );

    cards.forEach(function (card) {

        card.addEventListener("mouseenter", function () {

            card.style.transform =
                "translateY(-6px)";

        });

        card.addEventListener("mouseleave", function () {

            card.style.transform =
                "translateY(0px)";

        });

    });


    /*
    ==========================================
    TABLE ROW ANIMATION
    ==========================================
    */

    const tableRows = document.querySelectorAll(
        ".dashboard-table tbody tr"
    );

    tableRows.forEach(function (row, index) {

        row.style.opacity = "0";
        row.style.transform = "translateY(15px)";

        setTimeout(function () {

            row.style.transition =
                "all 0.4s ease";

            row.style.opacity = "1";
            row.style.transform =
                "translateY(0px)";

        }, index * 80);

    });


    /*
    ==========================================
    ACTION CARD CLICK EFFECT
    ==========================================
    */

    const actionCards = document.querySelectorAll(
        ".action-card"
    );

    actionCards.forEach(function (card) {

        card.addEventListener("click", function () {

            card.style.transform =
                "scale(0.98)";

            setTimeout(function () {

                card.style.transform =
                    "";

            }, 150);

        });

    });


    /*
    ==========================================
    BUTTON RIPPLE EFFECT
    ==========================================
    */

    const buttons = document.querySelectorAll(
        ".btn-main, .btn-light-action, .btn-view"
    );

    buttons.forEach(function (button) {

        button.addEventListener("click", function () {

            button.style.opacity = "0.8";

            setTimeout(function () {

                button.style.opacity = "1";

            }, 200);

        });

    });


    /*
    ==========================================
    STATUS BADGE COLORS
    ==========================================
    */

    const badges = document.querySelectorAll(
        ".status-badge"
    );

    badges.forEach(function (badge) {

        const text =
            badge.innerText.trim().toLowerCase();

        if (text.includes("active")) {

            badge.classList.add("status-active");

        } else if (text.includes("expired")) {

            badge.classList.add("status-expired");

        } else if (text.includes("draft")) {

            badge.classList.add("status-draft");

        } else {

            badge.classList.add("status-inactive");

        }

    });


    /*
    ==========================================
    PAGE LOADER EFFECT
    ==========================================
    */

    document.body.style.opacity = "0";

    setTimeout(function () {

        document.body.style.transition =
            "opacity 0.4s ease";

        document.body.style.opacity = "1";

    }, 100);


    /*
    ==========================================
    DASHBOARD CONSOLE LOG
    ==========================================
    */

    console.log(
        "Government Scheme Admin Dashboard Loaded Successfully"
    );

});