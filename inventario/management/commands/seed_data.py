from django.core.management.base import BaseCommand
from inventario.models import Producto


PRODUCTOS = [
    # Servicios
    {'sku': 'SERV-HORA', 'nombre': 'Hora de servicio técnico', 'descripcion': 'Por hora de trabajo técnico', 'precio_compra': 0, 'precio_venta': 25000, 'stock_actual': 9999, 'stock_minimo': 1},
    {'sku': 'SERV-DIAG', 'nombre': 'Diagnóstico de equipo', 'descripcion': 'Revisión y diagnóstico de falla', 'precio_compra': 0, 'precio_venta': 15000, 'stock_actual': 9999, 'stock_minimo': 1},
    {'sku': 'SERV-INST', 'nombre': 'Instalación de software', 'descripcion': 'Instalación de SO, office, etc.', 'precio_compra': 0, 'precio_venta': 20000, 'stock_actual': 9999, 'stock_minimo': 1},
    {'sku': 'SERV-MANT', 'nombre': 'Mantenimiento preventivo', 'descripcion': 'Limpieza, pasta térmica, revisión general', 'precio_compra': 0, 'precio_venta': 35000, 'stock_actual': 9999, 'stock_minimo': 1},
    {'sku': 'SERV-URG', 'nombre': 'Servicio de urgencia', 'descripcion': 'Atención prioritaria (recargo)', 'precio_compra': 0, 'precio_venta': 45000, 'stock_actual': 9999, 'stock_minimo': 1},
    {'sku': 'SERV-VISITA', 'nombre': 'Visita a domicilio/empresa', 'descripcion': 'Desplazamiento + primera hora', 'precio_compra': 0, 'precio_venta': 30000, 'stock_actual': 9999, 'stock_minimo': 1},

    # Almacenamiento
    {'sku': 'SSD-240', 'nombre': 'Disco SSD 240GB', 'descripcion': 'SSD SATA 240GB', 'precio_compra': 20000, 'precio_venta': 35000, 'stock_actual': 5, 'stock_minimo': 2},
    {'sku': 'SSD-480', 'nombre': 'Disco SSD 480GB', 'descripcion': 'SSD SATA 480GB', 'precio_compra': 35000, 'precio_venta': 55000, 'stock_actual': 5, 'stock_minimo': 2},
    {'sku': 'SSD-1TB', 'nombre': 'Disco SSD 1TB', 'descripcion': 'SSD SATA 1TB', 'precio_compra': 60000, 'precio_venta': 85000, 'stock_actual': 3, 'stock_minimo': 1},
    {'sku': 'NVME-500', 'nombre': 'Disco NVMe 500GB', 'descripcion': 'SSD M.2 NVMe 500GB', 'precio_compra': 45000, 'precio_venta': 65000, 'stock_actual': 3, 'stock_minimo': 1},
    {'sku': 'HDD-1TB', 'nombre': 'Disco Duro 1TB', 'descripcion': 'HDD SATA 1TB 7200rpm', 'precio_compra': 25000, 'precio_venta': 40000, 'stock_actual': 4, 'stock_minimo': 2},

    # Memoria RAM
    {'sku': 'RAM-4GB', 'nombre': 'Memoria RAM DDR4 4GB', 'descripcion': 'Módulo DDR4 4GB', 'precio_compra': 8000, 'precio_venta': 15000, 'stock_actual': 6, 'stock_minimo': 2},
    {'sku': 'RAM-8GB', 'nombre': 'Memoria RAM DDR4 8GB', 'descripcion': 'Módulo DDR4 8GB', 'precio_compra': 14000, 'precio_venta': 25000, 'stock_actual': 6, 'stock_minimo': 2},
    {'sku': 'RAM-16GB', 'nombre': 'Memoria RAM DDR4 16GB', 'descripcion': 'Módulo DDR4 16GB', 'precio_compra': 28000, 'precio_venta': 45000, 'stock_actual': 4, 'stock_minimo': 1},
    {'sku': 'RAM-8GB-DDR3', 'nombre': 'Memoria RAM DDR3 8GB', 'descripcion': 'Módulo DDR3 8GB', 'precio_compra': 10000, 'precio_venta': 18000, 'stock_actual': 4, 'stock_minimo': 2},

    # Fuentes de poder
    {'sku': 'FUENTE-500', 'nombre': 'Fuente de poder 500W', 'descripcion': 'Fuente ATX 500W 80+', 'precio_compra': 25000, 'precio_venta': 45000, 'stock_actual': 3, 'stock_minimo': 1},
    {'sku': 'FUENTE-600', 'nombre': 'Fuente de poder 600W', 'descripcion': 'Fuente ATX 600W 80+', 'precio_compra': 35000, 'precio_venta': 55000, 'stock_actual': 2, 'stock_minimo': 1},

    # Insumos
    {'sku': 'PASTA-TERM', 'nombre': 'Pasta térmica', 'descripcion': 'Pasta térmica para procesador', 'precio_compra': 3000, 'precio_venta': 8000, 'stock_actual': 10, 'stock_minimo': 3},
    {'sku': 'CABLE-HDMI', 'nombre': 'Cable HDMI 1.5m', 'descripcion': 'Cable HDMI estándar', 'precio_compra': 2500, 'precio_venta': 6000, 'stock_actual': 10, 'stock_minimo': 3},
    {'sku': 'CABLE-RED', 'nombre': 'Cable de red UTP 2m', 'descripcion': 'Cable Ethernet Cat5e', 'precio_compra': 1500, 'precio_venta': 4000, 'stock_actual': 10, 'stock_minimo': 3},
    {'sku': 'TECLADO-USB', 'nombre': 'Teclado USB', 'descripcion': 'Teclado USB estándar', 'precio_compra': 5000, 'precio_venta': 12000, 'stock_actual': 5, 'stock_minimo': 2},
    {'sku': 'MOUSE-USB', 'nombre': 'Mouse USB', 'descripcion': 'Mouse óptico USB', 'precio_compra': 3000, 'precio_venta': 8000, 'stock_actual': 5, 'stock_minimo': 2},
    {'sku': 'BATERIA-CMOS', 'nombre': 'Batería CMOS CR2032', 'descripcion': 'Batería para placa madre', 'precio_compra': 500, 'precio_venta': 2000, 'stock_actual': 20, 'stock_minimo': 5},
    {'sku': 'LIMP-CONTAC', 'nombre': 'Limpiador de contactos', 'descripcion': 'Spray limpiador de contactos electrónicos', 'precio_compra': 3000, 'precio_venta': 7000, 'stock_actual': 5, 'stock_minimo': 2},

    # Red
    {'sku': 'WIFI-USB', 'nombre': 'Adaptador WiFi USB', 'descripcion': 'Adaptador WiFi USB AC1200', 'precio_compra': 7000, 'precio_venta': 15000, 'stock_actual': 4, 'stock_minimo': 2},
    {'sku': 'SWITCH-5P', 'nombre': 'Switch 5 puertos Gigabit', 'descripcion': 'Switch Ethernet 10/100/1000', 'precio_compra': 10000, 'precio_venta': 20000, 'stock_actual': 3, 'stock_minimo': 1},
]


class Command(BaseCommand):
    help = 'Carga productos y servicios genéricos del rubro informático'

    def handle(self, *args, **options):
        created = 0
        skipped = 0
        for data in PRODUCTOS:
            _, was_created = Producto.objects.get_or_create(
                sku=data['sku'],
                defaults=data,
            )
            if was_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(f'Productos creados: {created}'))
        self.stdout.write(f'Productos existentes (omitidos): {skipped}')
        self.stdout.write(f'Total: {created + skipped}')
