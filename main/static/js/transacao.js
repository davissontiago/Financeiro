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

document.addEventListener('DOMContentLoaded', function() {
    const tipoSelect = document.querySelector('select[name="tipo"]');
    const categoriaSelect = document.querySelector('select[name="categoria"]');
    
    // Guardamos todas as opções originais na memória ao carregar a página
    const todasCategorias = Array.from(categoriaSelect.options);

    function filtrarCategorias() {
        const tipoSelecionado = tipoSelect.value; // 'D' ou 'R'
        
        // Salva qual categoria estava selecionada antes de limpar
        const valorSelecionadoAnterior = categoriaSelect.value;

        // Limpa o select atual
        categoriaSelect.innerHTML = '';

        todasCategorias.forEach(option => {
            // Mantém sempre a opção vazia "---------"
            if (option.value === '') {
                categoriaSelect.appendChild(option);
                return;
            }

            // Verifica o emoji no texto da opção (definido no forms.py)
            const isDespesa = option.text.includes('🔴');
            const isReceita = option.text.includes('🟢');

            // Lógica de exibição
            if ((tipoSelecionado === 'D' && isDespesa) || (tipoSelecionado === 'R' && isReceita)) {
                categoriaSelect.appendChild(option);
            }
        });

        // Tenta manter a seleção anterior se ela ainda for válida para o novo tipo
        // Caso contrário, volta para o vazio
        if (!Array.from(categoriaSelect.options).some(opt => opt.value === valorSelecionadoAnterior)) {
            categoriaSelect.value = '';
        } else {
            categoriaSelect.value = valorSelecionadoAnterior;
        }
    }

    // Escuta mudanças no campo Tipo (Despesa/Receita)
    tipoSelect.addEventListener('change', filtrarCategorias);
    
    // Executa uma vez ao abrir a página (importante para Edição)
    filtrarCategorias();
});