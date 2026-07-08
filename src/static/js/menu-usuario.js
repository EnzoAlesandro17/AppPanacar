document.addEventListener("DOMContentLoaded", () => {
    const boton = document.getElementById("usuario-boton");
    const menu = document.getElementById("usuario-dropdown");
    if (!boton || !menu) return;

    function cerrar() {
        menu.hidden = true;
        boton.setAttribute("aria-expanded", "false");
    }

    function abrir() {
        menu.hidden = false;
        boton.setAttribute("aria-expanded", "true");
    }

    boton.addEventListener("click", (evento) => {
        evento.stopPropagation();
        menu.hidden ? abrir() : cerrar();
    });

    document.addEventListener("click", (evento) => {
        if (!menu.hidden && !menu.contains(evento.target)) cerrar();
    });

    document.addEventListener("keydown", (evento) => {
        if (evento.key === "Escape") cerrar();
    });
});
