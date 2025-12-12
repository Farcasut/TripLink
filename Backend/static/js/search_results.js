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

burger.addEventListener("click", () => {
    const isOpen = !sidebar.classList.contains("-translate-x-full");
    isOpen ? closeSidebar() : openSidebar();
});

overlay.addEventListener("click", closeSidebar);
