from django import forms
from .models import Transacao, Categoria

class TransacaoForm(forms.ModelForm):
    parcelas = forms.IntegerField(
        required=False, 
        initial=1, 
        min_value=1, 
        max_value=48,
        label="Qtd. Parcelas",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
        
    class Meta:
        model = Transacao
        fields = ['tipo', 'valor', 'data', 'metodo', 'categoria', 'descricao']
        widgets = {
            'data': forms.DateInput(format='%Y-%m-%d',attrs={'type': 'date', 'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'placeholder': '0.00'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'metodo': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 1. Filtra as categorias do usuário e ordena por nome
        categorias = Categoria.objects.filter(usuario=user).order_by('nome')
        self.fields['categoria'].queryset = categorias

        # 2. Criamos as opções manualmente para incluir o tipo no texto ou lógica
        # Vamos usar o prefixo de emoji no texto para o JS identificar facilmente
        choices = [('', '---------')]
        for cat in categorias:
            prefixo = '🔴' if cat.tipo == 'D' else '🟢'
            choices.append((cat.id, f"{prefixo} {cat.nome}"))
        
        self.fields['categoria'].choices = choices

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'tipo', 'cor', 'ignorar_grafico']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nova categoria (ex: Lazer)'
            }),
            'cor': forms.TextInput(attrs={
                'type': 'color', 
                'class': 'form-control form-control-color', 
                'title': 'Escolha uma cor'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'ignorar_grafico': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'width: 20px; height: 20px;'}),
        
        }