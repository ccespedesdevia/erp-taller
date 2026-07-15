from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from datetime import date, timedelta
from ordenes.models import OrdenServicio
from cotizaciones.models import Configuracion


class Command(BaseCommand):
    help = "Envía alerta de tickets sin movimiento"

    def handle(self, *args, **options):
        config = Configuracion.obtener()
        now = date.today()
        inactivos = OrdenServicio.objects.filter(
            estado__in=['pendiente', 'en_curso'],
            updated_at__lte=now - timedelta(days=7)
        ).select_related('cliente')

        if not inactivos.exists():
            self.stdout.write("Sin tickets inactivos")
            return

        items = [f"TKT {o.codigo_seguimiento} - {o.cliente.razon_social} - Técnico: {o.tecnico or '-'} - Último: {o.updated_at.strftime('%d/%m')}" for o in inactivos]
        cuerpo = "Tickets sin movimiento en más de 7 días:\n\n" + "\n".join(items)

        send_mail(
            subject=f"[CACD] {inactivos.count()} ticket(s) inactivos",
            message=cuerpo,
            from_email=config.email,
            recipient_list=[config.email],
            fail_silently=True,
        )
        self.stdout.write(f"Alerta enviada: {inactivos.count()} tickets inactivos")
