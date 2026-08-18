document.addEventListener("DOMContentLoaded", function () {
    const actionButtons = document.querySelectorAll(
        ".btn, .action-btn"
    );

    const sections = document.querySelectorAll(
        ".section, .info-box, .card"
    );

    function animatePageLoad() {
        document.body.style.opacity = "0";

        setTimeout(function () {
            document.body.style.transition = "opacity 0.4s ease";
            document.body.style.opacity = "1";
        }, 100);
    }

    function animateSections() {
        sections.forEach(function (section, index) {
            section.style.opacity = "0";
            section.style.transform = "translateY(14px)";

            setTimeout(function () {
                section.style.transition = "all 0.45s ease";
                section.style.opacity = "1";
                section.style.transform = "translateY(0)";
            }, index * 80);
        });
    }

    function addButtonLoadingEffect() {
        actionButtons.forEach(function (button) {
            button.addEventListener("click", function () {
                const href = button.getAttribute("href") || "";

                if (
                    href.startsWith("http") ||
                    button.hasAttribute("target")
                ) {
                    return;
                }

                button.classList.add("btn-loading");
            });
        });
    }

    function addExternalLinkSafety() {
        const externalLinks = document.querySelectorAll('a[target="_blank"]');

        externalLinks.forEach(function (link) {
            if (!link.getAttribute("rel")) {
                link.setAttribute("rel", "noopener noreferrer");
            }
        });
    }

    function addCopySchemeCodeFeature() {
        const infoBoxes = document.querySelectorAll(".info-box");

        infoBoxes.forEach(function (box) {
            const label = box.querySelector(".info-label");
            const value = box.querySelector(".info-value");

            if (!label || !value) return;

            const labelText = label.textContent.trim().toLowerCase();

            if (labelText !== "scheme code") return;

            box.style.cursor = "pointer";
            box.setAttribute("title", "Click to copy scheme code");

            box.addEventListener("click", function () {
                const code = value.textContent.trim();

                if (!code || code === "-") return;

                if (navigator.clipboard) {
                    navigator.clipboard.writeText(code).then(function () {
                        const oldText = value.textContent;
                        value.textContent = "Copied!";

                        setTimeout(function () {
                            value.textContent = oldText;
                        }, 1200);
                    });
                }
            });
        });
    }

    function addShareButton() {
        const titleElement = document.querySelector(".main-title");
        const title = titleElement
            ? titleElement.textContent.trim()
            : "Government Scheme";

        const actions = document.querySelector(".actions");

        if (!actions) return;

        const shareButton = document.createElement("button");
        shareButton.type = "button";
        shareButton.className = "action-btn secondary-btn";
        shareButton.innerHTML =
            '<i class="fa-solid fa-share-nodes"></i> Share Scheme';

        shareButton.addEventListener("click", function () {
            const url = window.location.href;

            if (navigator.share) {
                navigator.share({
                    title: title,
                    text: "Check this government scheme on Smart Sheti",
                    url: url
                }).catch(function () {
                    // Share cancelled
                });

                return;
            }

            if (navigator.clipboard) {
                navigator.clipboard.writeText(url).then(function () {
                    const oldHTML = shareButton.innerHTML;
                    shareButton.innerHTML =
                        '<i class="fa-solid fa-check"></i> Link Copied';

                    setTimeout(function () {
                        shareButton.innerHTML = oldHTML;
                    }, 2000);
                });
            }
        });

        actions.appendChild(shareButton);
    }

    function highlightExpiredDate() {
        const labels = document.querySelectorAll(".info-box");

        labels.forEach(function (box) {
            const label = box.querySelector(".info-label");
            const value = box.querySelector(".info-value");

            if (!label || !value) return;

            if (label.textContent.trim().toLowerCase() !== "end date") {
                return;
            }

            const text = value.textContent.trim().toLowerCase();

            if (text === "ongoing" || text === "-") {
                return;
            }

            const parsedDate = new Date(text);

            if (Number.isNaN(parsedDate.getTime())) {
                return;
            }

            const today = new Date();
            today.setHours(0, 0, 0, 0);

            if (parsedDate < today) {
                box.classList.add("expired-date-box");
            }
        });
    }

    animatePageLoad();
    animateSections();
    addButtonLoadingEffect();
    addExternalLinkSafety();
    addCopySchemeCodeFeature();
    addShareButton();
    highlightExpiredDate();
});