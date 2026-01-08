from django.contrib import admin
from django.urls import path
from main import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('nova/', views.nova_transacao, name='nova_transacao'),
    path('categorias/', views.gerenciar_categorias, name='gerenciar_categorias'),
    path('categorias/excluir/<int:id>/', views.excluir_categoria, name='excluir_categoria'),
    path('transacao/excluir/<int:id>/', views.excluir_transacao, name='excluir_transacao'),
    path('transacao/editar/<int:id>/', views.editar_transacao, name='editar_transacao'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]