// ==================== SISTEMA DE FILTROS ====================
const filterCategorias = document.querySelectorAll('.filter-categoria');
const filterAlergenos = document.querySelectorAll('.filter-alergeno');
const platos = document.querySelectorAll('.plato');
const searchInput = document.getElementById('search');
    //MENU
if (platos.length > 0) {
    function aplicarFiltros() {
        const categoriasSeleccionadas = Array.from(filterCategorias)
            .filter(cb => cb.checked)
            .map(cb => cb.value);

        const alejenosSeleccionados = Array.from(filterAlergenos)
            .filter(cb => cb.checked)
            .map(cb => cb.value);

        const textoBusqueda = searchInput.value.toLowerCase();

        platos.forEach(plato => {
            let mostrar = true;

            // Filtro por categoría
            const categoria = plato.getAttribute('data-category');
            if (categoriasSeleccionadas.length > 0 && !categoriasSeleccionadas.includes(categoria)) {
                mostrar = false;
            }

            // Filtro por alérgenos (ocultar si el plato contiene alguno seleccionado)
            if (alejenosSeleccionados.length > 0) {
                const tags = plato.querySelectorAll('[data-alergeno]');
                const tieneAlergeno = Array.from(tags).some(tag =>
                    alejenosSeleccionados.includes(tag.getAttribute('data-alergeno'))
                );
                if (tieneAlergeno) {
                    mostrar = false;
                }
            }

            // Filtro por búsqueda
            if (textoBusqueda.length > 0) {
                const nombre = plato.querySelector('h3').textContent.toLowerCase();
                const descripcion = plato.querySelector('p').textContent.toLowerCase();
                if (!nombre.includes(textoBusqueda) && !descripcion.includes(textoBusqueda)) {
                    mostrar = false;
                }
            }

            plato.style.display = mostrar ? 'flex' : 'none';
        });
    }

    filterCategorias.forEach(checkbox => {
        checkbox.addEventListener('change', aplicarFiltros);
    });

    filterAlergenos.forEach(checkbox => {
        checkbox.addEventListener('change', aplicarFiltros);
    });

    searchInput.addEventListener('input', aplicarFiltros);
}
