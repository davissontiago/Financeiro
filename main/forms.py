from django import forms
from .models import Transacao, Categoria

class TransacaoForm(forms.ModelForm):
    class Meta:
        model = Transacao
        fields = ['tipo', 'valor', 'data', 'categoria', 'descricao']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}), 
            'valor': forms.NumberInput(attrs={'step': '0.01'}),
        }
    def __init__(self, user, *args, **kwargs):
        super(TransacaoForm, self).__init__(*args, **kwargs)
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