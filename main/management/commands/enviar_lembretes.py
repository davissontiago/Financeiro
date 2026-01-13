from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from webpush import send_user_notification
from django.utils import timezone

class Command(BaseCommand):
    help = 'Envia lembretes para todos os usuários'

    def handle(self, *args, **kwargs):
        # Exemplo: Enviar apenas se for depois das 18h
        # if timezone.now().hour < 18: return

        users = User.objects.all()
        payload = {
            "head": "Fechamento do Dia 🌙",
            "body": "Você teve algum gasto hoje? Clique para registrar.",
            "url": "/"
        }

        for user in users:
            # O 'send_user_notification' já verifica se o user tem inscrição
            try:
                send_user_notification(user=user, payload=payload, ttl=1000)
                self.stdout.write(f"Enviado para {user.username}")
            except:
                pass