from django.test import TestCase
from .models import ActivoFijo


class ActivoFijoTest(TestCase):
    def test_crear_activo(self):
        a = ActivoFijo.objects.create(nombre='Notebook Dell Inspiron', valor=850000)
        self.assertEqual(str(a), 'Notebook Dell Inspiron (Operativo)')
        self.assertEqual(a.estado, 'operativo')
