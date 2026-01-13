from django.contrib import admin
from django.urls import path, include
from main import views
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('nova/', views.nova_transacao, name='nova_transacao'),
    path('transacao/excluir/<int:id>/', views.excluir_transacao, name='excluir_transacao'),
    path('transacao/editar/<int:id>/', views.editar_transacao, name='editar_transacao'),
    
    path('categorias/', views.gerenciar_categorias, name='gerenciar_categorias'),
    path('categorias/nova/', views.nova_categoria, name='nova_categoria'),
    path('categorias/excluir/<int:id>/', views.excluir_categoria, name='excluir_categoria'),
    path('categorias/editar/<int:id>/', views.editar_categoria, name='editar_categoria'),
    
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('sw.js', TemplateView.as_view(template_name='main/sw.js', content_type='application/javascript'), name='sw.js'),
    path('webpush/', include('webpush.urls')),
]