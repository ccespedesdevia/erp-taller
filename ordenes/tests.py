from django.test import TestCase
from clientes.models import Cliente
from equipos.models import Equipo
from inventario.models import Producto
from .models import OrdenServicio, RepuestoUsado


class OrdenServicioTest(TestCase):
    def setUp(self):
        self.cliente = Cliente.objects.create(razon_social='Test SA', rut='1.234.567-8')
        self.equipo = Equipo.objects.create(cliente=self.cliente, tipo='pc', marca='Dell')
        self.producto = Producto.objects.create(sku='DISC-001', nombre='Disco SSD 480GB', stock_actual=5, precio_venta=45000)

    def test_crear_orden(self):
        os = OrdenServicio.objects.create(cliente=self.cliente, diagnostico='No enciende')
        self.assertEqual(str(os), f'OS #{os.id} - Test SA')
        self.assertEqual(os.estado, 'pendiente')

    def test_garantia_automatica(self):
        os = OrdenServicio.objects.create(cliente=self.cliente, equipo=self.equipo)
        os.estado = 'completado'
        os.save()
        self.assertIsNotNone(os.garantia_fin)

    def test_repuesto_descuenta_stock(self):
        os = OrdenServicio.objects.create(cliente=self.cliente, equipo=self.equipo)
        RepuestoUsado.objects.create(orden=os, producto=self.producto, cantidad=2, precio_unitario=45000)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_actual, 3)
