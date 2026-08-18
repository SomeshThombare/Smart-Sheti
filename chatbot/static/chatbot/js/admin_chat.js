document.addEventListener("DOMContentLoaded", function () {
    const chatWindow = document.getElementById("chatWindow");
    const messageInput = document.getElementById("messageInput");
    const chatForm = document.getElementById("chatForm");
    const quickPrompts = document.querySelectorAll(".quick-prompt");
    const alerts = document.querySelectorAll(".alert");

    const imageInput = document.getElementById("imageInput");
    const pdfInput = document.getElementById("pdfInput");
    const fileName = document.getElementById("fileName");

    if (chatWindow) {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    quickPrompts.forEach(function (button) {
        button.addEventListener("click", function () {
            if (messageInput) {
                messageInput.value = button.textContent.trim();
                messageInput.focus();
            }
        });
    });

    function updateFileName() {
        let names = [];

        if (imageInput && imageInput.files.length > 0) {
            names.push("Image: " + imageInput.files[0].name);
        }

        if (pdfInput && pdfInput.files.length > 0) {
            names.push("PDF: " + pdfInput.files[0].name);
        }

        if (fileName) {
            fileName.textContent = names.join(" | ");
        }
    }

    if (imageInput) {
        imageInput.addEventListener("change", updateFileName);
    }

    if (pdfInput) {
        pdfInput.addEventListener("change", updateFileName);
    }

    alerts.forEach(function (alertBox) {
        setTimeout(function () {
            alertBox.style.transition = "0.4s ease";
            alertBox.style.opacity = "0";
            alertBox.style.transform = "translateY(-8px)";

            setTimeout(function () {
                alertBox.remove();
            }, 450);
        }, 3000);
    });

    if (messageInput && chatForm) {
        messageInput.addEventListener("keydown", function (event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();

                if (messageInput.value.trim() !== "") {
                    chatForm.submit();
                }
            }
        });
    }

    if (chatForm) {
        chatForm.addEventListener("submit", function () {
            const submitBtn = chatForm.querySelector(".send-btn");

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending...';
            }
        });
    }
});