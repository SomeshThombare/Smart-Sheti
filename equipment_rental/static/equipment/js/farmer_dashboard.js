document.addEventListener("DOMContentLoaded", function () {

    // Animate stat numbers
    const counters = document.querySelectorAll(".stat-card h3");

    counters.forEach(counter => {
        const target = parseInt(counter.innerText) || 0;
        let count = 0;

        const updateCounter = () => {
            const increment = Math.ceil(target / 30);

            if (count < target) {
                count += increment;

                if (count > target) {
                    count = target;
                }

                counter.innerText = count;
                setTimeout(updateCounter, 30);
            }
        };

        updateCounter();
    });

    // Action card hover effect
    const cards = document.querySelectorAll(".action-card");

    cards.forEach(card => {
        card.addEventListener("mouseenter", () => {
            card.style.transform = "translateY(-6px)";
        });

        card.addEventListener("mouseleave", () => {
            card.style.transform = "translateY(0)";
        });
    });

    // Auto hide alerts
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = "0";
            alert.style.transition = "0.5s";

            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 3000);
    });

});