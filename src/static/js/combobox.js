document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-combobox]").forEach(iniciarCombobox);
});

function iniciarCombobox(contenedor) {
    const input = contenedor.querySelector("[data-combobox-input]");
    const idOculto = contenedor.querySelector("[data-combobox-id]");
    const modoOculto = contenedor.querySelector("[data-combobox-modo]");
    const lista = contenedor.querySelector("[data-combobox-lista]");
    const itemNuevo = lista.querySelector("[data-combobox-nuevo]");
    const textoBaseNuevo = itemNuevo.textContent.trim();
    const opciones = Array.from(lista.querySelectorAll("li[data-id]"));
    const bloqueNuevo = document.getElementById(contenedor.dataset.combobox);

    function mostrarLista() {
        const query = input.value.trim();
        const queryNorm = query.toLowerCase();
        opciones.forEach((li) => {
            li.hidden = queryNorm !== "" && !li.textContent.toLowerCase().includes(queryNorm);
        });
        itemNuevo.textContent = query ? `+ Agregar "${query}" como nuevo` : `+ ${textoBaseNuevo}`;
        lista.hidden = false;
    }

    function elegirExistente(li) {
        idOculto.value = li.dataset.id;
        modoOculto.value = "existente";
        input.value = li.dataset.texto;
        lista.hidden = true;
        if (bloqueNuevo) bloqueNuevo.hidden = true;
    }

    function elegirNuevo() {
        idOculto.value = "";
        modoOculto.value = "nuevo";
        lista.hidden = true;
        if (bloqueNuevo) bloqueNuevo.hidden = false;
    }

    input.addEventListener("input", mostrarLista);
    input.addEventListener("focus", mostrarLista);

    input.addEventListener("keydown", (evento) => {
        if (evento.key === "Enter") {
            evento.preventDefault();
            const primeraVisible = opciones.find((li) => !li.hidden);
            if (primeraVisible) elegirExistente(primeraVisible);
            else elegirNuevo();
        } else if (evento.key === "Escape") {
            lista.hidden = true;
        }
    });

    lista.addEventListener("click", (evento) => {
        const li = evento.target.closest("li");
        if (!li) return;
        if (li === itemNuevo) elegirNuevo();
        else elegirExistente(li);
    });

    input.addEventListener("blur", () => {
        setTimeout(() => { lista.hidden = true; }, 150);
    });

    document.addEventListener("click", (evento) => {
        if (!contenedor.contains(evento.target)) lista.hidden = true;
    });
}
