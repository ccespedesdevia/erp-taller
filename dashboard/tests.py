from django.test import TestCase
from django.contrib.auth.models import User


class DashboardViewTest(TestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)

    def test_dashboard_works_for_staff(self):
        user = User.objects.create_superuser('admin', 'admin@test.cl', 'admin123')
        self.client.force_login(user)
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)
