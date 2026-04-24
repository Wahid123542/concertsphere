document.addEventListener("DOMContentLoaded", () => {
    setTimeout(() => {
        document.querySelectorAll(".alert").forEach((el) => {
            const alertInstance = bootstrap.Alert.getOrCreateInstance(el);
            alertInstance.close();
        });
    }, 3500);

    const searchInputs = document.querySelectorAll(".table-search");
    searchInputs.forEach((input) => {
        input.addEventListener("keyup", function () {
            const query = this.value.toLowerCase();
            const table = this.closest(".card-body").querySelector(".searchable-table");
            if (!table) return;

            const rows = table.querySelectorAll("tbody tr");
            rows.forEach((row) => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(query) ? "" : "none";
            });
        });
    });
});