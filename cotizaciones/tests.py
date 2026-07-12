from django.test import TestCase
from clientes.models import Cliente
from .models import Cotizacion, ItemCotizacion


class CotizacionTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(razon_social='Test SA', rut='1.234.567-8')

    def test_crear_cotizacion(self):
        cot = Cotizacion.objects.create(cliente=self.cliente)
        self.assertEqual(str(cot), f'COT-{cot.numero:05d} - Test SA')

    def test_item_subtotal(self):
        cot = Cotizacion.objects.create(cliente=self.cliente)
        item = ItemCotizacion.objects.create(cotizacion=cot, descripcion='Hora de soporte', cantidad=3, precio_unitario=25000)
        self.assertEqual(item.subtotal(), 75000)
