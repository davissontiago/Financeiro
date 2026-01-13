import calendar, uuid
from datetime import date
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
from django.http import JsonResponse
from webpush import send_user_notification
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
    # =======================================================
    # 1. DEFINIÇÃO DE DATA E NAVEGAÇÃO
    # =======================================================
    hoje = timezone.now()
    mes_atual = int(request.GET.get('mes', hoje.month))
    ano_atual = int(request.GET.get('ano', hoje.year))
    
    data_exibicao = date(ano_atual, mes_atual, 1)

    # Navegação (Meses Anterior/Próximo)
    if mes_atual == 1:
        mes_ant, ano_ant = 12, ano_atual - 1
    else:
        mes_ant, ano_ant = mes_atual - 1, ano_atual

    if mes_atual == 12:
        mes_prox, ano_prox = 1, ano_atual + 1
    else:
        mes_prox, ano_prox = mes_atual + 1, ano_atual

    # =======================================================
    # 2. CONSULTA PRINCIPAL AO BANCO
    # =======================================================
    # select_related otimiza o carregamento das categorias
    transacoes = Transacao.objects.select_related('categoria').filter(
        usuario=request.user,
        data__month=mes_atual, 
        data__year=ano_atual
    ).order_by('-data', '-id')

    # =======================================================
    # 3. SEPARAÇÃO DAS LISTAS PARA EXIBIÇÃO
    # =======================================================
    
    # Lista 1: Receitas (Entradas)
    transacoes_receitas = transacoes.filter(tipo='R')

    # Lista 2: Despesas em Conta (Pix, Débito - Exclui Crédito e Receitas)
    transacoes_avista = transacoes.filter(tipo='D').exclude(metodo='C')

    # Lista 3: Despesas no Cartão de Crédito
    transacoes_credito = transacoes.filter(tipo='D', metodo='C')

    # =======================================================
    # 4. CÁLCULO DE SALDOS E TOTAIS
    # =======================================================
    
    # Soma das Receitas
    total_receitas = transacoes_receitas.aggregate(Sum('valor'))['valor__sum'] or 0
    
    # Soma das Despesas que saíram da conta (À vista/Débito)
    # Nota: Usamos a mesma lógica da lista 'avista' para manter consistência
    total_despesas = transacoes_avista.aggregate(Sum('valor'))['valor__sum'] or 0

    # Fatura Atual (Soma do que foi gasto no Crédito)
    fatura_atual = transacoes_credito.aggregate(Sum('valor'))['valor__sum'] or 0
    
    # Saldo (O que entrou - O que saiu da conta)
    saldo = total_receitas - total_despesas

    def somar_para_grafico(queryset):
        return queryset.exclude(categoria__ignorar_grafico=True).aggregate(Sum('valor'))['valor__sum'] or 0

    soma_grafico_receitas = somar_para_grafico(transacoes_receitas)
    soma_grafico_avista = somar_para_grafico(transacoes_avista)
    soma_grafico_credito = somar_para_grafico(transacoes_credito)
    
    # Total Geral de Despesas (Conta + Crédito) para o gráfico principal
    soma_grafico_total = transacoes.filter(tipo='D').exclude(categoria__ignorar_grafico=True).aggregate(Sum('valor'))['valor__sum'] or 0

    # =======================================================
    # 5. PREPARAÇÃO DOS GRÁFICOS
    # =======================================================
    def preparar_dados_grafico(queryset_filtrado):
        queryset_filtrado = queryset_filtrado.exclude(categoria__ignorar_grafico=True)
        dados_agrupados = queryset_filtrado.order_by().values('categoria__nome', 'categoria__cor').annotate(total=Sum('valor'))
        labels, data, cores = [], [], []
        for item in dados_agrupados:
            labels.append(item['categoria__nome'] or 'Outros')
            data.append(float(item['total']))
            cores.append(item['categoria__cor'] or '#CCCCCC')
        return labels, data, cores

    # Gera dados apenas para as despesas
    labels_v, data_v, cores_v = preparar_dados_grafico(transacoes_avista)
    labels_c, data_c, cores_c = preparar_dados_grafico(transacoes_credito)
    labels_r, data_r, cores_r = preparar_dados_grafico(transacoes_receitas)
    transacoes_total_despesas = transacoes.filter(tipo='D')
    labels_t, data_t, cores_t = preparar_dados_grafico(transacoes_total_despesas)
    soma_total_gastos = transacoes_total_despesas.aggregate(Sum('valor'))['valor__sum'] or 0

    # =======================================================
    # 6. CONTEXTO E RENDERIZAÇÃO
    # =======================================================
    context = {
        # Listas de Transações
        'transacoes_receitas': transacoes_receitas,
        'transacoes_avista': transacoes_avista,  
        'transacoes_credito': transacoes_credito,
        
        # Totais Financeiros
        'total_receitas': total_receitas,
        'total_despesas': total_despesas,
        'saldo': saldo,
        'fatura_atual': fatura_atual,
        'soma_grafico_receitas': soma_grafico_receitas,
        'soma_grafico_avista': soma_grafico_avista,
        'soma_grafico_credito': soma_grafico_credito,
        'soma_grafico_total': soma_grafico_total,

        # Dados dos Gráficos
        'soma_total_gastos': soma_total_gastos,

        'labels_receitas': labels_r, 'data_receitas': data_r, 'cores_receitas': cores_r,
        'labels_total': labels_t, 'data_total': data_t, 'cores_total': cores_t,
        'labels_avista': labels_v, 'data_avista': data_v, 'cores_avista': cores_v,
        'labels_credito': labels_c, 'data_credito': data_c, 'cores_credito': cores_c,
        
        # Navegação
        'data_exibicao': data_exibicao,
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
    categorias = Categoria.objects.filter(usuario=request.user)
    return render(request, 'main/categorias.html', {'categorias': categorias})

@login_required
def excluir_categoria(request, id):
    # Garante que só apaga se for do utilizador (usuario=request.user)
    categoria = get_object_or_404(Categoria, id=id, usuario=request.user)
    categoria.delete()
    return redirect('gerenciar_categorias')

@login_required
def nova_categoria(request):
    form = CategoriaForm(request.POST or None)
    
    if form.is_valid():
        cat = form.save(commit=False)
        cat.usuario = request.user
        cat.save()
        return redirect('gerenciar_categorias')
    
    # Reusa o template de formulário, passando o contexto "Nova"
    return render(request, 'main/form_categoria.html', {'form': form, 'acao': 'Nova'})

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
    return render(request, 'main/form_categoria.html', {'form': form, 'acao': 'Editar'})

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

def cron_lembretes(request):
    # Pega a hora atual (ajustada para o fuso horário configurado no settings)
    agora = timezone.localtime(timezone.now())
    hora = agora.hour
    
    # 1. Define a mensagem baseada no horário
    titulo = "Lembrete de Finanças"
    mensagem = "Não esqueça de registrar seus gastos!"
    icon = "/static/img/icon.png"

    if 11 <= hora < 14: # Faixa das 12h (Almoço)
        titulo = "🍽️ Hora do Almoço"
        mensagem = "Comprou quentinha ou lanche? Registre agora e mantenha o controle!"
        
    elif 17 <= hora < 19: # Faixa das 18h (Saída)
        titulo = "🌆 Fim de Expediente"
        mensagem = "Passou no mercado na volta para casa? Anote para não esquecer."
        
    elif 20 <= hora < 23: # Faixa das 21h (Fechamento)
        titulo = "🌙 Fechamento do Dia"
        mensagem = "Tire um minuto para revisar se anotou tudo hoje. O saldo bateu?"

    # 2. Envia para todos os usuários
    users = User.objects.all()
    enviados = 0
    
    payload = {
        "head": titulo,
        "body": mensagem,
        "icon": icon,
        "url": "/" # Ao clicar, abre a Home
    }

    for user in users:
        try:
            # O send_user_notification já verifica se o usuário tem inscrição
            send_user_notification(user=user, payload=payload, ttl=1000)
            enviados += 1
        except Exception as e:
            pass # Se falhar um, continua para o próximo
            
    return JsonResponse({'status': 'sucesso', 'mensagem': titulo, 'enviados': enviados})