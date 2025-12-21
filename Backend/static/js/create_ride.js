// Sidebar Toggle
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

// City Autocomplete
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

// Form Submission
const message = document.getElementById("message");
const form = document.getElementById("createRideForm");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const source = formData.get("source");
    const destination = formData.get("destination");
    const date = formData.get("date");
    const time = formData.get("time");
    const available_seats = parseInt(formData.get("available_seats"));
    const price = parseInt(formData.get("price"));

    // Validate cities are different
    if (source === destination) {
        message.innerHTML = '<p>Departure and arrival cities must be different</p>';
        message.classList.remove('hidden', 'bg-green-500', 'text-white');
        message.classList.add('bg-red-500', 'text-red-100');
        return;
    }

    // Combine date and time into Unix timestamp
    const dateTimeString = `${date}T${time}`;
    const departure_date = Math.floor(new Date(dateTimeString).getTime() / 1000);

    try {
        const response = await fetch("/rides/create", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include",
            body: JSON.stringify({
                source,
                destination,
                departure_date,
                price,
                available_seats
            })
        });

        const result = await response.json();

        message.classList.remove("hidden");
        message.innerHTML = `<p>${result.message}</p>`;

        if (result.status === "success") {
            message.classList.remove("bg-red-500", "text-red-100");
            message.classList.add("bg-green-500", "text-white");
            
            form.reset();
            
            setTimeout(() => {
                window.location.href = "/rides/all_rides";
            }, 500);
        } else {
            message.classList.remove("bg-green-500", "text-white");
            message.classList.add("bg-red-500", "text-red-100");
        }

        message.scrollIntoView({ behavior: "smooth", block: "nearest" });

    } catch (error) {
        message.classList.remove("hidden", "bg-green-500", "text-white");
        message.classList.add("bg-red-500", "text-red-100");
        message.innerHTML = `<p>Error: ${error.message}</p>`;
    }
});