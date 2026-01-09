import datetime, calendar, uuid
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from .models import Transacao, Categoria
from .forms import TransacaoForm, CategoriaForm

def add_months(source_date, months):
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

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
    form = TransacaoForm(request.user, request.POST or None)
    
    if form.is_valid():
        transacao_base = form.save(commit=False)
        transacao_base.usuario = request.user
        
        # Pega a quantidade de parcelas do formulário
        qtd_parcelas = form.cleaned_data.get('parcelas', 1) or 1
        
        # LÓGICA DO PARCELAMENTO
        if transacao_base.tipo == 'D' and transacao_base.metodo == 'C' and qtd_parcelas > 1:
            valor_total = transacao_base.valor
            valor_parcela = valor_total / qtd_parcelas
            data_inicial = transacao_base.data
            
            # Gera um ID único para este grupo de parcelas
            grupo_id = uuid.uuid4()
            
            for i in range(qtd_parcelas):
                Transacao.objects.create(
                    usuario=request.user,
                    descricao=transacao_base.descricao,
                    valor=valor_parcela,
                    categoria=transacao_base.categoria,
                    tipo='D',
                    metodo='C',
                    # relativedelta soma meses corretamente (ex: 31/jan + 1 mês = 28/fev)
                    data=data_inicial + relativedelta(months=i),
                    
                    # Vínculo do grupo
                    id_parcelamento=grupo_id,
                    parcela_atual=i+1,
                    parcela_total=qtd_parcelas
                )
        else:
            # Compra à vista ou comum
            transacao_base.save()
        
        return redirect(f'/?mes={transacao_base.data.month}&ano={transacao_base.data.year}')
    
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
def editar_categoria(request, id):
    # Busca a categoria (garantindo que pertence ao usuário logado)
    categoria = get_object_or_404(Categoria, id=id, usuario=request.user)
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            return redirect('gerenciar_categorias')
    else:
        form = CategoriaForm(instance=categoria)
    
    # Vamos usar um template separado para não misturar com a lista
    return render(request, 'main/form_categoria.html', {'form': form})

@login_required
def excluir_transacao(request, id):
    transacao = get_object_or_404(Transacao, id=id, usuario=request.user)
    
    # Se tem id_parcelamento, apaga TODAS as irmãs
    if transacao.id_parcelamento:
        Transacao.objects.filter(id_parcelamento=transacao.id_parcelamento).delete()
    else:
        transacao.delete()
        
    return redirect('home')

@login_required
def editar_transacao(request, id):
    transacao_atual = get_object_or_404(Transacao, id=id, usuario=request.user)
    
    # Se for POST, vamos SALVAR
    if request.method == 'POST':
        form = TransacaoForm(request.user, request.POST)
        if form.is_valid():
            # 1. Apaga a transação antiga (e o grupo dela se existir)
            if transacao_atual.id_parcelamento:
                Transacao.objects.filter(id_parcelamento=transacao_atual.id_parcelamento).delete()
            else:
                transacao_atual.delete()
            
            # 2. Recria como se fosse nova (usa a mesma lógica da nova_transacao)
            nova = form.save(commit=False)
            nova.usuario = request.user
            qtd_parcelas = form.cleaned_data.get('parcelas', 1) or 1
            
            if nova.tipo == 'D' and nova.metodo == 'C' and qtd_parcelas > 1:
                valor_parcela = nova.valor / qtd_parcelas
                grupo_id = uuid.uuid4()
                for i in range(qtd_parcelas):
                    Transacao.objects.create(
                        usuario=request.user,
                        descricao=nova.descricao,
                        valor=valor_parcela,
                        categoria=nova.categoria,
                        tipo='D',
                        metodo='C',
                        data=nova.data + relativedelta(months=i),
                        id_parcelamento=grupo_id,
                        parcela_atual=i+1,
                        parcela_total=qtd_parcelas
                    )
            else:
                nova.save()
                
            return redirect('home')

    # Se for GET (Abrir o formulário), PREPARAMOS OS DADOS
    else:
        dados_iniciais = {
            'descricao': transacao_atual.descricao,
            'categoria': transacao_atual.categoria,
            'tipo': transacao_atual.tipo,
            'metodo': transacao_atual.metodo,
        }

        # Se for parcelado, precisamos SOMAR tudo para mostrar o valor TOTAL da compra
        if transacao_atual.id_parcelamento:
            grupo = Transacao.objects.filter(id_parcelamento=transacao_atual.id_parcelamento)
            valor_total_compra = grupo.aggregate(Sum('valor'))['valor__sum']
            primeira_parcela = grupo.order_by('data').first()
            
            dados_iniciais['valor'] = valor_total_compra
            dados_iniciais['data'] = primeira_parcela.data
            dados_iniciais['parcelas'] = transacao_atual.parcela_total # Preenche o campo de parcelas
        else:
            dados_iniciais['valor'] = transacao_atual.valor
            dados_iniciais['data'] = transacao_atual.data
            dados_iniciais['parcelas'] = 1

        # Carrega o form com esses dados calculados
        form = TransacaoForm(request.user, initial=dados_iniciais)
    
    return render(request, 'main/form_transacao.html', {'form': form, 'acao': 'Editar'})