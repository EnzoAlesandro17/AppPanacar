const OJO_ABIERTO = '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7Z"/><circle cx="12" cy="12" r="3"/>';
const OJO_CERRADO =
    '<path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-11-8-11-8a21.8 21.8 0 0 1 5.06-6.94M9.9 4.24A10.4 10.4 0 0 1 12 4c7 0 11 8 11 8a21.8 21.8 0 0 1-2.16 3.19M14.12 14.12a3 3 0 1 1-4.24-4.24"/><path d="M1 1l22 22"/>';

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".btn-mostrar-password").forEach((boton) => {
        const campo = document.getElementById(boton.dataset.target);
        const icono = boton.querySelector(".icono-ojo");
        if (!campo || !icono) return;

        boton.addEventListener("click", () => {
            const mostrando = campo.type === "text";
            campo.type = mostrando ? "password" : "text";
            boton.setAttribute("aria-pressed", String(!mostrando));
            boton.setAttribute("aria-label", mostrando ? "Mostrar contraseña" : "Ocultar contraseña");
            icono.innerHTML = mostrando ? OJO_ABIERTO : OJO_CERRADO;
        });
    });
});
