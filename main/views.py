import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.db.models import Sum
from django.utils import timezone
from .models import Transacao, Categoria
from .forms import TransacaoForm, CategoriaForm

@login_required
def home(request):
    # 1. Descobrir qual mês/ano mostrar
    hoje = timezone.now()
    
    # Tenta pegar da URL (ex: ?mes=2&ano=2024), se não tiver, usa o atual
    mes_atual = int(request.GET.get('mes', hoje.month))
    ano_atual = int(request.GET.get('ano', hoje.year))

    # Lista manual para garantir meses em Português e Capitalizados
    lista_meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    }
    nome_mes_exibicao = lista_meses[mes_atual]

    # 2. Filtrar as transações DO MÊS ESPECÍFICO E DO UTILIZADOR
    transacoes = Transacao.objects.filter(
        usuario=request.user,  # <--- Filtro de segurança
        data__month=mes_atual, 
        data__year=ano_atual
    ).order_by('-data') # Mais recentes primeiro

    # 3. Calcular Totais (Baseado SOMENTE no filtro acima)
    total_receitas = transacoes.filter(tipo='R').aggregate(Sum('valor'))['valor__sum'] or 0
    total_despesas = transacoes.filter(tipo='D').aggregate(Sum('valor'))['valor__sum'] or 0
    saldo = total_receitas - total_despesas

    # 4. Dados para o Gráfico (Baseado SOMENTE no filtro acima)
    gastos_por_categoria = transacoes.filter(tipo='D').values('categoria__nome', 'categoria__cor').annotate(total=Sum('valor'))
    
    labels = []
    data_grafico = []
    cores = []

    for item in gastos_por_categoria:
        labels.append(item['categoria__nome'] if item['categoria__nome'] else 'Outros')
        data_grafico.append(float(item['total']))
        cores.append(item['categoria__cor'] if item['categoria__cor'] else '#CCCCCC')

    # 5. Lógica de Navegação (Mês Anterior / Próximo)
    # Anterior
    if mes_atual == 1:
        mes_ant, ano_ant = 12, ano_atual - 1
    else:
        mes_ant, ano_ant = mes_atual - 1, ano_atual

    # Próximo
    if mes_atual == 12:
        mes_prox, ano_prox = 1, ano_atual + 1
    else:
        mes_prox, ano_prox = mes_atual + 1, ano_atual

    context = {
        'transacoes': transacoes,
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'saldo': saldo,
        'labels_grafico': labels,
        'data_grafico': data_grafico,
        'cores_grafico': cores,
        
        # Variáveis de Navegação
        'nome_mes_exibicao': nome_mes_exibicao, # Nome bonito
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
