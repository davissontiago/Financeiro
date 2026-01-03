from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
    
class Categoria(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=50)
    cor = models.CharField(max_length=7, default='#6c757d') 
    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} ({self.usuario.username})"

class Transacao(models.Model):
    TIPO_CHOICES = (
        ('D', 'Despesa'),
        ('R', 'Receita'),
    )
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    descricao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Descrição")
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField(default=timezone.now)
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES, default='D')
    
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    

    def __str__(self):
        return f"{self.descricao} - {self.usuario.username}"