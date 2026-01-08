import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from .models import Transacao, Categoria
from .forms import TransacaoForm, CategoriaForm

@login_required
def home(request):
    # 1. Definição de Data (Mês/Ano)
    hoje = timezone.now()
    mes_atual = int(request.GET.get('mes', hoje.month))
    ano_atual = int(request.GET.get('ano', hoje.year))

    # Nomes dos meses
    lista_meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    nome_mes_exibicao = lista_meses[mes_atual]

    # 2. Navegação (Meses Anterior/Próximo)
    if mes_atual == 1:
        mes_ant, ano_ant = 12, ano_atual - 1
    else:
        mes_ant, ano_ant = mes_atual - 1, ano_atual

    if mes_atual == 12:
        mes_prox, ano_prox = 1, ano_atual + 1
    else:
        mes_prox, ano_prox = mes_atual + 1, ano_atual

    # =======================================================
    # DADOS DO MÊS ATUAL
    # =======================================================
    transacoes = Transacao.objects.filter(
        usuario=request.user,
        data__month=mes_atual, 
        data__year=ano_atual
    ).order_by('-data', '-id')

    # Função auxiliar de gráficos
    def preparar_dados_grafico(queryset_filtrado):
        dados_agrupados = queryset_filtrado.order_by().values('categoria__nome', 'categoria__cor').annotate(total=Sum('valor'))
        labels, data, cores = [], [], []
        for item in dados_agrupados:
            labels.append(item['categoria__nome'] or 'Outros')
            data.append(float(item['total']))
            cores.append(item['categoria__cor'] or '#CCCCCC')
        return labels, data, cores

    # GRÁFICOS (Apenas informativo)
    labels_v, data_v, cores_v = preparar_dados_grafico(transacoes.filter(tipo='D', metodo='V'))
    labels_c, data_c, cores_c = preparar_dados_grafico(transacoes.filter(tipo='D', metodo='C'))

    # =======================================================
    # CÁLCULO DE SALDO (SIMPLIFICADO E CORRETO)
    # =======================================================
    
    # Receitas (Dinheiro que entrou)
    total_receitas = transacoes.filter(tipo='R').aggregate(Sum('valor'))['valor__sum'] or 0
    
    # Despesas (Dinheiro que SAIU da conta DE FATO neste mês)
    # Isso inclui gastos no débito E pagamentos de fatura que você registrar manualmente
    total_despesas = transacoes.filter(tipo='D', metodo='V').aggregate(Sum('valor'))['valor__sum'] or 0
    
    # Saldo Real
    saldo = total_receitas - total_despesas

    # Fatura Acumulada (Apenas para você saber quanto já gastou no crédito este mês)
    fatura_atual = transacoes.filter(tipo='D', metodo='C').aggregate(Sum('valor'))['valor__sum'] or 0


    soma_avista = transacoes.filter(tipo='D', metodo='V').aggregate(Sum('valor'))['valor__sum'] or 0

    # 2. Gráfico Crédito (Fatura Atual)
    soma_credito = transacoes.filter(tipo='D', metodo='C').aggregate(Sum('valor'))['valor__sum'] or 0

    # ... (Cálculo de Saldo e Totais Gerais mantidos igual ao passo anterior) ...

    context = {
        'transacoes': transacoes,
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'saldo': saldo,
        'fatura_atual': fatura_atual,
        
        # Totais específicos para os gráficos (Para desenhar no meio)
        'soma_avista': soma_avista,
        'soma_credito': soma_credito,

        # Gráficos
        'labels_avista': labels_v, 'data_avista': data_v, 'cores_avista': cores_v,
        'labels_credito': labels_c, 'data_credito': data_c, 'cores_credito': cores_c,
        
        # Navegação
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

@login_required
def editar_transacao(request, id):
    transacao = get_object_or_404(Transacao, id=id, usuario=request.user)
    
    if request.method == 'POST':
        # CORREÇÃO: Passamos request.user como primeiro argumento
        form = TransacaoForm(request.user, request.POST, instance=transacao)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        # CORREÇÃO: Passamos request.user aqui também
        form = TransacaoForm(request.user, instance=transacao)
    
    return render(request, 'main/form_transacao.html', {'form': form, 'acao': 'Editar'})