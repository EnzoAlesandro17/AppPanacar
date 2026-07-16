document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-buscador]").forEach(iniciarBuscador);
});

function iniciarBuscador(input) {
    const objetivo = document.getElementById(input.dataset.buscador);
    if (!objetivo) return;

    const items = objetivo.tagName === "SELECT"
        ? Array.from(objetivo.querySelectorAll("option")).filter((opcion) => opcion.value)
        : Array.from(objetivo.querySelectorAll("tbody tr"));

    input.addEventListener("input", () => {
        const query = input.value.trim().toLowerCase();
        items.forEach((item) => {
            item.hidden = query !== "" && !item.textContent.toLowerCase().includes(query);
        });
    });
}
