const overlay = document.getElementById("overlay");
const burger = document.getElementById("burgerBtn");
const sidebar = document.getElementById("sidebar");

function openSidebar() {
    sidebar.classList.remove("-translate-x-full");
    overlay.classList.remove("hidden");
}

function closeSidebar() {
    sidebar.classList.add("-translate-x-full");
    overlay.classList.add("hidden");
}

burger?.addEventListener("click", () => {
    sidebar.classList.contains("-translate-x-full")
        ? openSidebar()
        : closeSidebar();
});

overlay?.addEventListener("click", closeSidebar);

document.addEventListener("DOMContentLoaded", () => {
    const msg = document.getElementById("bookingMsg");

    document.querySelectorAll(".book-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
            const rideId = btn.dataset.rideId;

            btn.disabled = true;
            btn.textContent = "Sending...";

            try {
                const res = await fetch(`/rides/book/${rideId}`, {
                    method: "POST",
                    credentials: "include"
                });

                const data = await res.json();
                msg.classList.remove("hidden");

                if (res.ok) {
                    msg.className = "mb-4 p-3 rounded bg-green-100 text-green-700";
                    msg.textContent = "Booking request sent.";
                    btn.textContent = "Requested";
                    btn.classList.add("opacity-60", "cursor-not-allowed");
                } else {
                    msg.className = "mb-4 p-3 rounded bg-red-100 text-red-700";
                    msg.textContent = data.message || "Booking failed.";
                    btn.disabled = false;
                    btn.textContent = "Book Ride";
                }
            } catch {
                msg.className = "mb-4 p-3 rounded bg-red-100 text-red-700";
                msg.textContent = "Network error.";
                btn.disabled = false;
                btn.textContent = "Book Ride";
            }
        });
    });
});
