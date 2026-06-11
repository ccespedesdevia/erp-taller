from django.test import TestCase
from .models import Producto


class ProductoModelTest(TestCase):
    def test_stock_bajo(self):
        p = Producto.objects.create(sku='MON-001', nombre='Monitor 24"', stock_actual=2, stock_minimo=5)
        self.assertTrue(p.stock_bajo())

    def test_stock_normal(self):
        p = Producto.objects.create(sku='TCL-001', nombre='Teclado', stock_actual=10, stock_minimo=5)
        self.assertFalse(p.stock_bajo())

    def test_str(self):
        p = Producto.objects.create(sku='USB-001', nombre='Pendrive 32GB')
        self.assertIn('USB-001', str(p))
