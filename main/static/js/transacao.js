document.addEventListener('DOMContentLoaded', function() {
    const campoTipo = document.querySelector('select[name="tipo"]');
    const divMetodo = document.getElementById('div-metodo');

    function atualizarVisibilidade() {
        if (!campoTipo || !divMetodo) return; // Segurança

        // Se for 'D' (Despesa), mostra o método. Senão, esconde.
        if (campoTipo.value === 'D') {
            divMetodo.style.display = 'block';
        } else {
            divMetodo.style.display = 'none';
        }
    }

    // Inicializa
    atualizarVisibilidade();

    // Monitora mudanças
    if (campoTipo) {
        campoTipo.addEventListener('change', atualizarVisibilidade);
    }
});