document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-reorder-url]").forEach(iniciarReorden);
});

function iniciarReorden(tbody) {
    const url = tbody.dataset.reorderUrl;
    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    tbody.querySelectorAll(".drag-handle").forEach((manija) => {
        manija.addEventListener("pointerdown", (evento) => iniciarArrastre(evento, tbody, url, csrfToken));
    });
}

function iniciarArrastre(evento, tbody, url, csrfToken) {
    const fila = evento.target.closest("tr[data-id]");
    if (!fila) return;
    evento.preventDefault();
    fila.classList.add("arrastrando");

    function alMover(eventoMove) {
        const debajo = document.elementFromPoint(eventoMove.clientX, eventoMove.clientY);
        const filaDebajo = debajo ? debajo.closest("tr[data-id]") : null;
        if (!filaDebajo || filaDebajo === fila || filaDebajo.parentNode !== tbody) return;

        const rect = filaDebajo.getBoundingClientRect();
        const despuesDeMedio = eventoMove.clientY - rect.top > rect.height / 2;
        tbody.insertBefore(fila, despuesDeMedio ? filaDebajo.nextSibling : filaDebajo);
    }

    function alSoltar() {
        fila.classList.remove("arrastrando");
        document.removeEventListener("pointermove", alMover);
        document.removeEventListener("pointerup", alSoltar);
        guardarOrden(tbody, url, csrfToken);
    }

    document.addEventListener("pointermove", alMover);
    document.addEventListener("pointerup", alSoltar);
}

function guardarOrden(tbody, url, csrfToken) {
    const ids = Array.from(tbody.querySelectorAll("tr[data-id]")).map((fila) => fila.dataset.id);
    fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify({ orden: ids }),
    });
}
