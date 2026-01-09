// dashboard.js

// Registra plugins do Chart.js se estiverem carregados
if (typeof Chart !== 'undefined' && typeof ChartDataLabels !== 'undefined') {
    Chart.register(ChartDataLabels);

    // Plugin para Texto no Centro
    const centerTextPlugin = {
        id: 'centerText',
        beforeDraw: function(chart) {
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

// Função Genérica para Criar Gráficos
function criarGraficoFinanceiro(canvasId, labels, data, cores, totalValor, msgVazia) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    const formatarMoeda = (valor) => {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
    };

    // Converte string python (ex: "1000,50") para float se necessário
    // Mas aqui esperamos que totalValor venha formatado ou número
    // Se vier do Django como string formatada (float), parseamos:
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
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '75%', 
                elements: {
                    center: {
                        text: textoTotal
                    }
                },
                plugins: {
                    legend: { position: 'bottom', labels: { boxWidth: 12, padding: 15 } },
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
                    datalabels: {
                        color: '#fff',
                        font: { weight: 'bold', size: 11 },
                        formatter: (value, ctx) => {
                            let sum = 0;
                            ctx.chart.data.datasets[0].data.map(d => sum += d);
                            let percentage = (value * 100 / sum);
                            return percentage > 5 ? percentage.toFixed(0) + "%" : "";
                        }
                    }
                }
            }
        });
    } else {
        document.getElementById(canvasId).parentElement.innerHTML = 
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