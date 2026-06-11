from django.test import TestCase
from .models import Cliente, Contacto


class ClienteModelTest(TestCase):
    def test_crear_cliente(self):
        c = Cliente.objects.create(razon_social='Empresa Ltda', rut='12.345.678-9')
        self.assertEqual(str(c), 'Empresa Ltda (12.345.678-9)')

    def test_crear_contacto(self):
        c = Cliente.objects.create(razon_social='Test SA', rut='98.765.432-1')
        ct = Contacto.objects.create(cliente=c, nombre='Juan Pérez', es_principal=True)
        self.assertEqual(str(ct), 'Juan Pérez - Test SA')
        self.assertEqual(c.contactos.count(), 1)
