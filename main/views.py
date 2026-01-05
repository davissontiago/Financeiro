import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from .models import Transacao, Categoria
from .forms import TransacaoForm, CategoriaForm

@login_required
def home(request):
    # 1. Descobrir qual mês/ano mostrar
    hoje = timezone.now()
    mes_atual = int(request.GET.get('mes', hoje.month))
    ano_atual = int(request.GET.get('ano', hoje.year))

    # Lista manual para garantir meses em Português
    lista_meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    nome_mes_exibicao = lista_meses[mes_atual]

    # 2. Filtro Principal: Transações do USUÁRIO e do MÊS específico
    transacoes = Transacao.objects.filter(
        usuario=request.user,
        data__month=mes_atual, 
        data__year=ano_atual
    ).order_by('-data')

    # 3. Calcular Totais Gerais
    total_receitas = transacoes.filter(tipo='R').aggregate(Sum('valor'))['valor__sum'] or 0
    total_despesas = transacoes.filter(tipo='D').aggregate(Sum('valor'))['valor__sum'] or 0
    despesas_avista = transacoes.filter(tipo='D', metodo='V').aggregate(Sum('valor'))['valor__sum'] or 0
    saldo = total_receitas - despesas_avista
    saldo = total_receitas - total_despesas

    # 4. Preparação dos Dados para os Gráficos (Função Auxiliar Interna)
    def preparar_dados_grafico(queryset_filtrado):
        # Agrupa por Categoria e soma os valores
        dados_agrupados = queryset_filtrado.values('categoria__nome', 'categoria__cor').annotate(total=Sum('valor'))
        
        labels, data, cores = [], [], []
        for item in dados_agrupados:
            labels.append(item['categoria__nome'] if item['categoria__nome'] else 'Outros')
            data.append(float(item['total']))
            cores.append(item['categoria__cor'] if item['categoria__cor'] else '#CCCCCC')
        return labels, data, cores

    # --- Gráfico 1: À Vista / Débito ---
    # Filtra apenas despesas (tipo='D') que são à vista (metodo='V')
    gastos_avista = transacoes.filter(tipo='D', metodo='V')
    labels_v, data_v, cores_v = preparar_dados_grafico(gastos_avista)

    # --- Gráfico 2: Cartão de Crédito ---
    # Filtra apenas despesas (tipo='D') que são crédito (metodo='C')
    gastos_credito = transacoes.filter(tipo='D', metodo='C')
    labels_c, data_c, cores_c = preparar_dados_grafico(gastos_credito)

    # 5. Lógica de Navegação (Mês Anterior / Próximo)
    if mes_atual == 1:
        mes_ant, ano_ant = 12, ano_atual - 1
    else:
        mes_ant, ano_ant = mes_atual - 1, ano_atual

    if mes_atual == 12:
        mes_prox, ano_prox = 1, ano_atual + 1
    else:
        mes_prox, ano_prox = mes_atual + 1, ano_atual

    context = {
        'transacoes': transacoes,
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'saldo': saldo,
        
        # Dados para o Gráfico À Vista
        'labels_avista': labels_v,
        'data_avista': data_v,
        'cores_avista': cores_v,

        # Dados para o Gráfico Crédito
        'labels_credito': labels_c,
        'data_credito': data_c,
        'cores_credito': cores_c,
        
        # Variáveis de Navegação e Título
        'nome_mes_exibicao': nome_mes_exibicao,
        'ano_atual': ano_atual,
        'mes_ant': mes_ant, 'ano_ant': ano_ant,
        'mes_prox': mes_prox, 'ano_prox': ano_prox,
    }
    
    return render(request, 'main/home.html', context)

@login_required
def nova_transacao(request):
    # Passamos request.user para o form filtrar as categorias corretamente
    form = TransacaoForm(request.user, request.POST or None)
    
    if form.is_valid():
        t = form.save(commit=False) # Não salva ainda
        t.usuario = request.user    # Atribui o dono da transação
        t.save()                    # Salva agora
        
        # Redireciona para o mês da transação criada
        return redirect(f'/?mes={t.data.month}&ano={t.data.year}')
    
    return render(request, 'main/form_transacao.html', {'form': form})

@login_required
def gerenciar_categorias(request):
    # Filtra apenas categorias do utilizador logado
    categorias = Categoria.objects.filter(usuario=request.user)
    form = CategoriaForm(request.POST or None)
    
    if form.is_valid():
        cat = form.save(commit=False)
        cat.usuario = request.user # Atribui o dono da categoria
        cat.save()
        return redirect('gerenciar_categorias')

    return render(request, 'main/categorias.html', {'categorias': categorias, 'form': form})

@login_required
def excluir_categoria(request, id):
    # Garante que só apaga se for do utilizador (usuario=request.user)
    categoria = get_object_or_404(Categoria, id=id, usuario=request.user)
    categoria.delete()
    return redirect('gerenciar_categorias')

@login_required
def excluir_transacao(request, id):
    # Garante que só apaga se for do utilizador
    transacao = get_object_or_404(Transacao, id=id, usuario=request.user)
    transacao.delete()
    return redirect('home')
