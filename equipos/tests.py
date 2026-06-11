from django.test import TestCase
from clientes.models import Cliente
from .models import Equipo


class EquipoModelTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(razon_social='Test SA', rut='1.234.567-8')

    def test_crear_equipo(self):
        e = Equipo.objects.create(cliente=self.cliente, tipo='notebook', marca='Lenovo', modelo='ThinkPad X1')
        self.assertIn('Notebook Lenovo ThinkPad X1', str(e))

    def test_equipo_con_serie(self):
        e = Equipo.objects.create(cliente=self.cliente, tipo='pc', marca='Dell', numero_serie='SN123')
        self.assertIn('[SN123]', str(e))
