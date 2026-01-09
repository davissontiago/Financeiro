document.addEventListener('DOMContentLoaded', function() {
    const campoTipo = document.querySelector('select[name="tipo"]');
    const campoMetodo = document.querySelector('select[name="metodo"]'); // Pega o campo método
    const divMetodo = document.getElementById('div-metodo');
    const divParcelas = document.getElementById('div-parcelas'); // Pega a div parcelas

    function atualizarVisibilidade() {
        if (!campoTipo || !divMetodo) return;

        // 1. Regra do Tipo (Despesa vs Receita)
        if (campoTipo.value === 'D') {
            divMetodo.style.display = 'block';
        } else {
            divMetodo.style.display = 'none';
            // Se escondeu o método, esconde a parcela tbm
            if (divParcelas) divParcelas.style.display = 'none'; 
            return; 
        }

        // 2. Regra do Método (Cartão vs Outros)
        // Só mostra parcelas se for Despesa (D) E Cartão de Crédito (C)
        if (campoMetodo && divParcelas) {
            if (campoMetodo.value === 'C') {
                divParcelas.style.display = 'block';
            } else {
                divParcelas.style.display = 'none';
                // Reseta para 1 se esconder, para evitar erros
                const inputParcela = divParcelas.querySelector('input');
                if (inputParcela) inputParcela.value = 1;
            }
        }
    }

    // Inicializa
    atualizarVisibilidade();

    // Monitora mudanças
    if (campoTipo) campoTipo.addEventListener('change', atualizarVisibilidade);
    if (campoMetodo) campoMetodo.addEventListener('change', atualizarVisibilidade);
});