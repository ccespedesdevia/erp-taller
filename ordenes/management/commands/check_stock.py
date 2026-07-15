from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.db.models import F
from inventario.models import Producto
from cotizaciones.models import Configuracion


class Command(BaseCommand):
    help = "Envía alerta de productos con stock crítico"

    def handle(self, *args, **options):
        config = Configuracion.obtener()
        bajo = Producto.objects.filter(stock_actual__lte=F('stock_minimo'))

        if not bajo.exists():
            self.stdout.write("Stock normal")
            return

        items = [f"{p.sku} - {p.nombre}: {p.stock_actual}/{p.stock_minimo}" for p in bajo]
        cuerpo = "Productos con stock crítico:\n\n" + "\n".join(items)

        send_mail(
            subject=f"[CACD] {bajo.count()} producto(s) con stock crítico",
            message=cuerpo,
            from_email=config.email,
            recipient_list=[config.email],
            fail_silently=True,
        )
        self.stdout.write(f"Alerta enviada: {bajo.count()} productos con stock bajo")
