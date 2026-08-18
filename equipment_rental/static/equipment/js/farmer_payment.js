document.addEventListener("DOMContentLoaded", function () {
    const payNowBtn = document.getElementById("payNowBtn");

    function getCookie(name) {
        let cookieValue = null;

        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");

            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();

                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(
                        cookie.substring(name.length + 1)
                    );
                    break;
                }
            }
        }

        return cookieValue;
    }

    function autoHideAlerts() {
        const alerts = document.querySelectorAll(".alert");

        alerts.forEach(function (alertBox) {
            setTimeout(function () {
                alertBox.style.transition = "all 0.5s ease";
                alertBox.style.opacity = "0";
                alertBox.style.transform = "translateY(-10px)";

                setTimeout(function () {
                    alertBox.remove();
                }, 500);
            }, 4000);
        });
    }

    function setButtonLoading(button, isLoading) {
        if (!button) {
            return;
        }

        if (isLoading) {
            button.disabled = true;
            button.dataset.originalText = button.innerHTML;
            button.innerHTML =
                '<i class="fas fa-spinner fa-spin"></i> Processing...';
        } else {
            button.disabled = false;

            if (button.dataset.originalText) {
                button.innerHTML = button.dataset.originalText;
            }
        }
    }

    async function postJson(url, data) {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
                "X-Requested-With": "XMLHttpRequest"
            },
            body: JSON.stringify(data || {})
        });

        const result = await response.json();

        if (!response.ok || result.status === "error") {
            const message =
                result.message ||
                result.errors?.detail?.[0] ||
                "Something went wrong.";

            throw new Error(message);
        }

        return result;
    }

    function showPageMessage(message, type) {
        const pageWrapper = document.querySelector(".page-wrapper");

        if (!pageWrapper) {
            alert(message);
            return;
        }

        const oldAlert = pageWrapper.querySelector(".dynamic-alert");

        if (oldAlert) {
            oldAlert.remove();
        }

        const alertBox = document.createElement("div");
        alertBox.className =
            "alert dynamic-alert " +
            (type === "success" ? "alert-success" : "alert-danger");

        alertBox.textContent = message;

        const paymentLayout = document.querySelector(".payment-layout");

        pageWrapper.insertBefore(alertBox, paymentLayout);

        setTimeout(function () {
            alertBox.style.transition = "all 0.5s ease";
            alertBox.style.opacity = "0";
            alertBox.style.transform = "translateY(-10px)";

            setTimeout(function () {
                alertBox.remove();
            }, 500);
        }, 4000);
    }

    function startRazorpayPayment(orderResult) {
        const data = orderResult.data || {};

        const options = {
            key: payNowBtn.dataset.keyId || data.razorpay_key_id || "",
            amount: data.amount,
            currency: data.currency || "INR",
            name: "Smart Sheti",
            description: "Equipment Booking Payment",
            order_id: data.razorpay_order_id || data.id,
            prefill: {
                name: payNowBtn.dataset.customerName || "",
                email: payNowBtn.dataset.customerEmail || "",
                contact: payNowBtn.dataset.customerPhone || ""
            },
            notes: {
                booking_code: payNowBtn.dataset.bookingCode || ""
            },
            theme: {
                color: "#2e7d32"
            },
            handler: async function (response) {
                try {
                    setButtonLoading(payNowBtn, true);

                    await postJson(payNowBtn.dataset.verifyUrl, {
                        razorpay_order_id: response.razorpay_order_id,
                        razorpay_payment_id: response.razorpay_payment_id,
                        razorpay_signature: response.razorpay_signature,
                        payment_method: "upi"
                    });

                    showPageMessage(
                        "Payment successful. Redirecting to booking details...",
                        "success"
                    );

                    window.location.href = payNowBtn.dataset.successUrl;
                } catch (error) {
                    setButtonLoading(payNowBtn, false);
                    showPageMessage(error.message || "Payment verification failed.", "error");
                }
            },
            modal: {
                ondismiss: function () {
                    setButtonLoading(payNowBtn, false);
                    showPageMessage(
                        "Payment cancelled. You can try again or go to My Bookings.",
                        "error"
                    );
                }
            }
        };

        const razorpay = new Razorpay(options);

        razorpay.on("payment.failed", function (response) {
            setButtonLoading(payNowBtn, false);

            const message =
                response.error && response.error.description
                    ? response.error.description
                    : "Payment failed. Please try again.";

            showPageMessage(message, "error");
        });

        razorpay.open();
    }

    if (payNowBtn) {
        payNowBtn.addEventListener("click", async function () {
            if (typeof Razorpay === "undefined") {
                showPageMessage("Razorpay checkout could not be loaded.", "error");
                return;
            }

            try {
                setButtonLoading(payNowBtn, true);

                const orderResult = await postJson(
                    payNowBtn.dataset.createOrderUrl,
                    {
                        booking_code: payNowBtn.dataset.bookingCode
                    }
                );

                startRazorpayPayment(orderResult);
            } catch (error) {
                setButtonLoading(payNowBtn, false);
                showPageMessage(error.message || "Unable to start payment.", "error");
            }
        });
    }

    autoHideAlerts();
});