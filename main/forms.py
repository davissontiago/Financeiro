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
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valor': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control', 'placeholder': '0.00'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'metodo': forms.Select(attrs={'class': 'form-select'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
        }
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = Categoria.objects.filter(usuario=user)

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'cor']
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
        
        }