document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-cancelar]").forEach((boton) => {
        boton.addEventListener("click", () => window.history.back());
    });
});
