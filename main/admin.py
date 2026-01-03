from django.contrib import admin
from .models import Categoria, Transacao

# Configuração para mostrar colunas úteis na listagem
class TransacaoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'valor', 'data', 'tipo', 'categoria', 'usuario')
    list_filter = ('tipo', 'data', 'usuario')
    search_fields = ('descricao',)

class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cor', 'usuario')
    list_filter = ('usuario',)

# Registra os modelos
admin.site.register(Transacao, TransacaoAdmin)
admin.site.register(Categoria, CategoriaAdmin)