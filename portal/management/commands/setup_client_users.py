from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from clientes.models import Cliente


class Command(BaseCommand):
    help = 'Crea usuarios de portal para clientes que no tengan uno'

    def add_arguments(self, parser):
        parser.add_argument('--password', default='cliente123', help='Contraseña por defecto para nuevos usuarios')

    def handle(self, *args, **options):
        password = options['password']
        created = 0
        already = 0
        skipped = 0

        for cliente in Cliente.objects.all():
            if cliente.user:
                already += 1
                continue
            if not cliente.email and not cliente.rut:
                skipped += 1
                self.stdout.write(self.style.WARNING(f'  Cliente #{cliente.id} "{cliente.razon_social}": sin email ni RUT, se omite'))
                continue

            username = cliente.rut.replace('.', '').replace('-', '').replace(' ', '')
            email = cliente.email or f'{username}@cliente.local'

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=cliente.razon_social[:30],
            )
            cliente.user = user
            cliente.save(update_fields=['user'])
            created += 1
            self.stdout.write(f'  Creado usuario "{username}" para {cliente.razon_social}')

        self.stdout.write(self.style.SUCCESS(f'\nUsuarios creados: {created}'))
        self.stdout.write(f'Ya tenían usuario: {already}')
        self.stdout.write(f'Omitidos (sin datos): {skipped}')
        self.stdout.write(f'\nContraseña por defecto: {password}')
        self.stdout.write('Los clientes ingresan en /portal/login/ con su RUT (solo números) y la contraseña.')
