from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from datetime import date, timedelta
from ordenes.models import OrdenServicio
from cotizaciones.models import Configuracion


class Command(BaseCommand):
    help = "Envía alerta de garantías próximas a vencer"

    def handle(self, *args, **options):
        config = Configuracion.obtener()
        now = date.today()
        prox = OrdenServicio.objects.filter(
            garantia_fin__gte=now,
            garantia_fin__lte=now + timedelta(days=7),
            estado__in=['completado', 'facturado']
        ).select_related('cliente')

        if not prox.exists():
            self.stdout.write("Sin garantías por vencer")
            return

        items = [f"TKT {o.codigo_seguimiento} - {o.cliente.razon_social} - Vence: {o.garantia_fin}" for o in prox]
        cuerpo = "Garantías próximas a vencer:\n\n" + "\n".join(items)

        send_mail(
            subject=f"[CACD] {prox.count()} garantía(s) por vencer",
            message=cuerpo,
            from_email=config.email,
            recipient_list=[config.email],
            fail_silently=True,
        )
        self.stdout.write(f"Alerta enviada: {prox.count()} garantías por vencer")
