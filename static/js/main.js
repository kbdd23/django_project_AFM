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

// ==================== ALTO REAL DEL HEADER ====================
// El hero mide "pantalla completa menos el header". El header cambia de
// alto al redimensionar (bajo los 720px pasa a dos filas), asi que en vez
// de un numero fijo en el CSS lo medimos en vivo y lo publicamos como
// variable CSS. El valor escrito en styles.css queda solo de respaldo.
(function () {
    'use strict';

    const encabezado = document.querySelector('.site-header');
    const hero = document.querySelector('.hero-carrusel');
    if (!encabezado || !hero) {
        return; // esta pagina no tiene hero a pantalla completa
    }

    function publicarAltoDelHeader() {
        document.documentElement.style.setProperty(
            '--altura-header-real',
            encabezado.offsetHeight + 'px'
        );
    }

    // ResizeObserver dispara cada vez que el header cambia de tamaño,
    // incluso si el cambio lo provoca un media query y no la ventana.
    new ResizeObserver(publicarAltoDelHeader).observe(encabezado);
    publicarAltoDelHeader();
})();
