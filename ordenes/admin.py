import json
import os
from django.contrib import admin
from django.utils.html import format_html
from .models import OrdenServicio, RepuestoUsado, FotoOrden, ComentarioTicket


class RepuestoUsadoInline(admin.TabularInline):
    model = RepuestoUsado
    extra = 1


class FotoOrdenInline(admin.TabularInline):
    model = FotoOrden
    extra = 1


class ComentarioInline(admin.TabularInline):
    model = ComentarioTicket
    extra = 1
    fields = ['autor', 'texto']
    verbose_name = 'Responder al cliente'
    verbose_name_plural = 'Conversación'

    def get_formset(self, request, obj=None, **kwargs):
        Formset = super().get_formset(request, obj, **kwargs)

        class ComentarioFormset(Formset):
            def save_new(self, form, commit=True):
                obj = form.save(commit=False)
                obj.es_tecnico = True
                if not obj.autor:
                    obj.autor = request.user.get_full_name() or request.user.username
                if commit:
                    obj.save()
                return obj

        return ComentarioFormset


@admin.register(OrdenServicio)
class OrdenServicioAdmin(admin.ModelAdmin):
    list_display = ['codigo_seguimiento', '__str__', 'estado', 'tecnico', 'oc_aprobada', 'fecha_ingreso', 'horas_trabajadas', 'garantia_fin']
    list_filter = ['estado', 'tecnico']
    search_fields = ['cliente__razon_social', 'equipo__numero_serie', 'tecnico']
    inlines = [RepuestoUsadoInline, FotoOrdenInline, ComentarioInline]
    fieldsets = (
        ('Cliente y Equipo', {'fields': ['cliente', 'equipo', 'tecnico']}),
        ('Contacto', {'fields': ['contacto', 'telefono', 'email_contacto', 'empresa', 'centro_costo']}),
        ('Fechas', {'fields': ['fecha_ingreso', 'fecha_inicio', 'fecha_termino', 'fecha_entrega']}),
        ('Trabajo', {'fields': ['motivo', 'diagnostico', 'trabajo_realizado', 'software_instalado']}),
        ('Horas y Garantía', {'fields': ['horas_trabajadas', 'estado', 'garantia_fin']}),
        ('Documentos', {'fields': ['orden_compra_cliente', 'orden_compra_archivo', 'oc_aprobada']}),
        ('Identificación de PC', {'fields': ['identificacion_html', 'archivo_identificacion']}),
        ('Interno', {'fields': ['notas_internas']}),
    )
    readonly_fields = ['fecha_ingreso', 'identificacion_html']

    def identificacion_html(self, obj):
        api = {}
        if obj.datos_identificacion:
            try:
                api = json.loads(obj.datos_identificacion)
            except:
                api = {'raw': obj.datos_identificacion}

        archivo = obj.archivo_identificacion
        html = '<div style="max-width:100%;overflow-x:auto;">'
        html += '<table style="width:100%;border-collapse:collapse;">'
        html += '<tr style="background:#f1f5f9;"><th style="padding:8px;border:1px solid #ddd;">Campo</th>'
        html += '<th style="padding:8px;border:1px solid #ddd;">Datos del sistema (API)</th>'
        html += '<th style="padding:8px;border:1px solid #ddd;">Informe subido</th></tr>'

        campos = [
            ('Hostname', 'hostname'),
            ('UUID BIOS', 'uuid_bios'),
            ('MAC Address', 'mac_address'),
            ('Disco Serial', 'disco_serial'),
            ('Motherboard', 'motherboard_serial'),
            ('Fabricante', 'fabricante'),
            ('Modelo', 'modelo_pc'),
            ('CPU', 'cpu'),
            ('RAM', 'ram_gb'),
            ('Disco', 'disco_modelo'),
            ('Windows', 'windows_version'),
            ('Arquitectura', 'arquitectura'),
        ]

        txt_data = {}
        if archivo and archivo.name.endswith('.txt'):
            try:
                ruta = archivo.path
                if os.path.exists(ruta):
                    with open(ruta, 'r') as f:
                        txt_data = self._parse_txt(f.read())
            except:
                pass

        for label, key in campos:
            v_api = api.get(key, '—')
            v_txt = txt_data.get(key, '—')
            match = v_api == v_txt or (not v_api and not v_txt)
            color = '#16a34a' if match else '#dc2626'
            bg = '#f0fdf4' if match else '#fef2f2'
            html += f'<tr style="background:{bg};">'
            html += f'<td style="padding:6px 8px;border:1px solid #ddd;font-weight:bold;">{label}</td>'
            html += f'<td style="padding:6px 8px;border:1px solid #ddd;color:{color};">{v_api or "—"}</td>'
            html += f'<td style="padding:6px 8px;border:1px solid #ddd;color:{color};">{v_txt or "—"}</td>'
            html += '</tr>'

        html += '</table></div>'
        if not api and not txt_data:
            return format_html('<span class="text-muted">Sin datos de identificación.</span>')
        return format_html(html)

    def _parse_txt(self, content):
        d = {}
        for line in content.splitlines():
            if ':' in line:
                key, val = line.split(':', 1)
                key = key.strip().lower()
                val = val.strip()
                if 'hostname' in key:
                    d['hostname'] = val
                elif 'fabricante' in key:
                    d['fabricante'] = val
                elif 'modelo' in key:
                    d['modelo_pc'] = val
                elif 'uuid' in key or 'bios' in key:
                    d['uuid_bios'] = val
                elif 'sistema' in key or 'windows' in key:
                    d['windows_version'] = val
        return d

    identificacion_html.short_description = 'Identificación'


admin.site.register(RepuestoUsado)
admin.site.register(FotoOrden)