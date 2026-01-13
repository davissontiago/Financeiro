from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import uuid
    
class Categoria(models.Model):
    TIPO_CHOICES = (
        ('D', 'Despesa'),
        ('R', 'Receita'),
    )
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=50)
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES, default='D')
    cor = models.CharField(max_length=7, default='#6c757d') 
    criada_em = models.DateTimeField(auto_now_add=True)
    
    ignorar_grafico = models.BooleanField(default=False, verbose_name="Ocultar nos Gráficos")

    def __str__(self):
        return f"{self.nome}"
    class Meta:
        ordering = ['nome']

class Transacao(models.Model):
    TIPO_CHOICES = (
        ('D', 'Despesa'),
        ('R', 'Receita'),
    )
    METODO_CHOICES = (
        ('V', 'Pix / Débito'),
        ('C', 'Cartão de Crédito'),
    )
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    descricao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Descrição")
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField(default=timezone.now)
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES, default='D')
    
    metodo = models.CharField(max_length=1, choices=METODO_CHOICES, default='V', verbose_name="Método")
    
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    
    id_parcelamento = models.UUIDField(null=True, blank=True) 

    parcela_atual = models.IntegerField(default=1)  
    parcela_total = models.IntegerField(default=1) 

    def __str__(self):
        if self.parcela_total > 1:
            return f"{self.descricao} ({self.parcela_atual}/{self.parcela_total})"
        return f"{self.descricao}"