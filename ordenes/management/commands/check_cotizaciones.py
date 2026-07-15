from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from datetime import date, timedelta
from cotizaciones.models import Cotizacion, Configuracion


class Command(BaseCommand):
    help = "Envía alerta de cotizaciones próximas a vencer"

    def handle(self, *args, **options):
        config = Configuracion.obtener()
        now = date.today()
        prox = Cotizacion.objects.filter(
            estado='enviada',
            valida_hasta__gte=now,
            valida_hasta__lte=now + timedelta(days=3)
        ).select_related('cliente')

        if not prox.exists():
            self.stdout.write("Sin cotizaciones por vencer")
            return

        items = [f"N°{c.numero:05d} - {c.cliente.razon_social} - ${c.total:,.0f} - Vence: {c.valida_hasta}" for c in prox]
        cuerpo = "Cotizaciones próximas a vencer:\n\n" + "\n".join(items)

        send_mail(
            subject=f"[CACD] {prox.count()} cotización(es) por vencer",
            message=cuerpo,
            from_email=config.email,
            recipient_list=[config.email],
            fail_silently=True,
        )
        self.stdout.write(f"Alerta enviada: {prox.count()} cotizaciones por vencer")
