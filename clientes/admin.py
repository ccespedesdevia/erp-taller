from django.contrib import admin
from .models import Cliente, Contacto


class ContactoInline(admin.TabularInline):
    model = Contacto
    extra = 1


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['razon_social', 'rut', 'telefono', 'email']
    search_fields = ['razon_social', 'rut', 'email']
    inlines = [ContactoInline]
