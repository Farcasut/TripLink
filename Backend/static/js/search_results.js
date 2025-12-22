const overlay = document.getElementById("overlay");
const burger = document.getElementById("burgerBtn");
const sidebar = document.getElementById("sidebar");

function openSidebar() {
  sidebar?.classList.remove("-translate-x-full");
  overlay?.classList.remove("hidden");
}

function closeSidebar() {
  sidebar?.classList.add("-translate-x-full");
  overlay?.classList.add("hidden");
}

burger?.addEventListener("click", () => {
  sidebar.classList.contains("-translate-x-full")
    ? openSidebar()
    : closeSidebar();
});

overlay?.addEventListener("click", closeSidebar);

document.addEventListener("DOMContentLoaded", () => {
  const msg = document.getElementById("bookingMsg");
  const buttons = document.querySelectorAll(".book-btn");

  if (!msg || buttons.length === 0) return;

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const rideId = btn.dataset.rideId;
      if (!rideId) return;

      btn.disabled = true;
      btn.textContent = "Sending...";

      fetch(`/bookings/request/${rideId}`, {
        method: "POST",
        credentials: "include",
      })
        .then((res) =>
          res.json().then((data) => ({ res, data }))
        )
        .then(({ res, data }) => {
          msg.classList.remove("hidden");

          if (res.ok) {
            msg.className = "mb-4 p-3 rounded bg-green-100 text-green-700";
            msg.textContent = "Booking request sent.";

            btn.textContent = "Already booked";
            btn.classList.remove("bg-secondary", "hover:bg-primary");
            btn.classList.add("bg-gray-400", "cursor-not-allowed");
            btn.disabled = true;
          } else {
            msg.className = "mb-4 p-3 rounded bg-red-100 text-red-700";
            msg.textContent = data.message || "Booking failed.";
            btn.disabled = false;
            btn.textContent = "Book Ride";
          }
        })
        .catch(() => {
          msg.className = "mb-4 p-3 rounded bg-red-100 text-red-700";
          msg.textContent = "Network error.";
          btn.disabled = false;
          btn.textContent = "Book Ride";
        });
    });
  });
});
