document.addEventListener("DOMContentLoaded", function () {
    const counters = document.querySelectorAll(".stat-card h3");

    counters.forEach(function (counter) {
        const target = parseInt(counter.innerText.trim()) || 0;
        let count = 0;

        if (target === 0) {
            counter.innerText = "0";
            return;
        }

        const increment = Math.max(1, Math.ceil(target / 35));

        function updateCounter() {
            count += increment;

            if (count >= target) {
                counter.innerText = target;
                return;
            }

            counter.innerText = count;
            setTimeout(updateCounter, 25);
        }

        updateCounter();
    });
});