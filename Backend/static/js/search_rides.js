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

let cityList = [];

async function loadCities(country) {
    try {
        const response = await fetch(`/cities/${country}`);
        if (!response.ok)
            throw new Error();

        const json = await response.json();
        cityList = json['content'];
    } catch {
        console.log('Cities are missing.');
    }
}

loadCities('romania');

function setupAutocomplete(inputId, resultsId) {
    const results = document.getElementById(resultsId);
    const input = document.getElementById(inputId);

    input.addEventListener("input", () => {
        const query = input.value.trim().toLowerCase();
        results.innerHTML = "";

        if (query.length === 0) {
            results.classList.add("hidden");
            return;
        }

        const matches = cityList.filter(city =>
            city.toLowerCase().startsWith(query)
        ).slice(0, 7);

        if (matches.length === 0) {
            results.classList.add("hidden");
            return;
        }

        matches.forEach(city => {
            const li = document.createElement("li");
            li.textContent = city;
            li.className = "px-3 py-2 hover:bg-gray-100 cursor-pointer";
            li.addEventListener("click", () => {
                input.value = city;
                results.classList.add("hidden");
            });
            
            results.appendChild(li);
        });

        results.classList.remove("hidden");
    });

    document.addEventListener("click", (e) => {
        if (!results.contains(e.target) && e.target !== input) {
            results.classList.add("hidden");
        }
    });
}

setupAutocomplete("fromCityInput", "fromCityResults");
setupAutocomplete("toCityInput", "toCityResults");
