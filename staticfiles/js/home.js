// dashboard.js

// Registra plugins do Chart.js se estiverem carregados
if (typeof Chart !== 'undefined' && typeof ChartDataLabels !== 'undefined') {
    Chart.register(ChartDataLabels);

    // Plugin para Texto no Centro
    const centerTextPlugin = {
        id: 'centerText',
        beforeDraw: function (chart) {
            if (chart.config.options.elements.center) {
                var width = chart.width,
                    height = chart.height,
                    ctx = chart.ctx;

                ctx.restore();

                var text = chart.config.options.elements.center.text;
                if (!text) return;
                text = text.toString();

                var fontSize = (height / 160).toFixed(2);
                if (text.length > 8) fontSize = (fontSize * 0.85).toFixed(2);
                if (text.length > 12) fontSize = (fontSize * 0.70).toFixed(2);

                ctx.font = "bold " + fontSize + "em sans-serif";
                ctx.textBaseline = "middle";
                ctx.fillStyle = "#333";

                var textX = Math.round((width - ctx.measureText(text).width) / 2);
                var textY = (height / 2) - (height * 0.05);

                ctx.fillText(text, textX, textY);
                ctx.save();
            }
        }
    };
    Chart.register(centerTextPlugin);
}

// main/static/js/home.js

// main/static/js/home.js

// 1. Limpeza preventiva
Chart.getChart = Chart.getChart;
if (Chart.registry && Chart.registry.plugins) {
    const pluginsGerais = ['centerText', 'center', 'centerTextCustom', 'meuTextoCentral', 'pluginCentroHomeDefinitivo', 'pluginCentroUnico_'];
    pluginsGerais.forEach(id => {
        try { Chart.unregister(Chart.registry.getPlugin(id)); } catch(e) {}
    });
}

function criarGraficoFinanceiro(canvasId, labels, data, cores, totalValor, msgVazia) {
    const canvasElement = document.getElementById(canvasId);
    if (!canvasElement) return;
    
    const instance = Chart.getChart(canvasId);
    if (instance) instance.destroy();

    const ctx = canvasElement.getContext('2d');
    
    const formatarMoeda = (valor) => {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
    };

    let valorNumerico = parseFloat(totalValor.toString().replace(',', '.'));
    const textoTotal = formatarMoeda(valorNumerico);

    if (labels && labels.length > 0) {
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: cores,
                    borderWidth: 1,
                    borderColor: '#fff', // Borda branca entre as fatias para separar
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%', 
                layout: {
                    padding: 0 
                },
                plugins: {
                    legend: { 
                        position: 'bottom', 
                        labels: { boxWidth: 12, padding: 15, font: { size: 11 } } 
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let value = context.raw;
                                let total = context.chart._metasets[context.datasetIndex].total;
                                let percentage = ((value / total) * 100).toFixed(1) + '%';
                                return context.label + ': ' + formatarMoeda(value) + ' (' + percentage + ')';
                            }
                        }
                    },
                    // === AQUI ESTÁ A MÁGICA DO DESTAQUE ===
                    datalabels: {
                        color: '#ffffff',                // Texto Branco Puro
                        textStrokeColor: 'rgba(0,0,0,0.6)', // Contorno Preto (60% opacidade)
                        textStrokeWidth: 3,              // Grossura do contorno (bem visível)
                        textShadowColor: 'rgba(0,0,0,0.3)', // Sombra extra para profundidade
                        textShadowBlur: 3,

                        font: { weight: '400', size: 10 }, // Peso 900 é "Extra Bold"
                        textAlign: 'center',
                        anchor: 'center',
                        align: 'center',
                        offset: 0,
                        
                        formatter: (value, context) => {
                            const dataset = context.chart.data.datasets[0];
                            const total = dataset.data.reduce((acc, curr) => acc + curr, 0);
                            const percent = (value * 100) / total;
                            
                            // Mantemos a regra de esconder fatias muito pequenas (menor que 4%)
                            // para não sobrepor, já que agora o texto está mais "gordo" com a borda.
                            if (percent < 3) return ""; 

                            return percent.toFixed(0) + "%";
                        }
                    }
                }
            },
            plugins: [ChartDataLabels, { 
                id: 'pluginCentroUnico_' + canvasId,
                afterDraw: function(chart) {
                    const { ctx, chartArea: { top, bottom, left, right } } = chart;
                    ctx.save();
                    const centerX = (left + right) / 2;
                    const centerY = (top + bottom) / 2;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.font = 'bold 14px sans-serif'; 
                    ctx.fillStyle = '#212529';
                    ctx.fillText(textoTotal, centerX, centerY);
                    ctx.restore();
                }
            }]
        });
    } else {
        canvasElement.parentElement.innerHTML = 
            '<div class="text-center mt-5 text-muted d-flex flex-column align-items-center justify-content-center h-100">' +
            '<span style="font-size: 2rem;">🍃</span>' +
            '<p class="mt-2">' + msgVazia + '</p>' +
            '</div>';
    }
}

function toggleDetails(element) {
    // Procura a div de detalhes DENTRO do elemento clicado
    const details = element.querySelector('.transaction-details');

    if (details) {
        // Alterna a classe d-none (esconde/mostra) do Bootstrap
        details.classList.toggle('d-none');
    }
}

// Função para alternar entre as abas de transações
function filtrarAba(tipo, botaoClicado) {
    // 1. Esconde TODAS as listas
    document.querySelectorAll('.lista-transacoes').forEach(el => {
        el.classList.add('d-none');
    });

    // 2. Mostra apenas a lista selecionada (conta, credito ou receitas)
    const listaAlvo = document.getElementById('aba-' + tipo);
    if (listaAlvo) {
        listaAlvo.classList.remove('d-none');
    }

    // 3. Reseta o estilo de TODOS os botões para "inativo" (outline)
    document.querySelectorAll('.btn-filtro').forEach(btn => {
        btn.classList.remove('btn-dark', 'active');
        btn.classList.add('btn-outline-secondary');
    });

    // 4. Aplica o estilo "ativo" (preenchido) apenas no botão clicado
    botaoClicado.classList.remove('btn-outline-secondary');
    botaoClicado.classList.add('btn-dark', 'active');
}