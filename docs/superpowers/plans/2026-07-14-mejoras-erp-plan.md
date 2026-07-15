# Mejoras ERP CACD Soluciones — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar 5 mejoras: dashboard ejecutivo con Chart.js, reportes financieros con margen, alertas inteligentes, recordatorios automáticos, y cálculo de margen real.

**Architecture:** Todo se construye sobre apps existentes (dashboard, ordenes, cotizaciones). Sin modelos nuevos. Chart.js v4 vía CDN. Management commands para recordatorios.

**Tech Stack:** Django 4.2, Chart.js 4, SQLite, Gmail SMTP, PythonAnywhere cron

---

### Task 1: Agregar campos a modelos

**Files:**
- Modify: `cotizaciones/models.py` (Configuracion - add costo_hora)
- Modify: `ordenes/models.py` (OrdenServicio - add horas_cobradas + propiedades)
- Create: `cotizaciones/migrations/0005_configuracion_costo_hora.py`
- Create: `ordenes/migrations/0006_ordenservicio_horas_cobradas.py`

- [ ] **Step 1: Agregar costo_hora a Configuracion**

Edit `cotizaciones/models.py`:
```python
# Dentro de class Configuracion, antes de ultimo_numero_cotizacion:
costo_hora = models.DecimalField(
    max_digits=12, decimal_places=0, default=40845,
    verbose_name="Costo por hora (CLP)",
    help_text="Costo por hora de servicio para cálculo de margen"
)
```

- [ ] **Step 2: Agregar horas_cobradas y propiedades a OrdenServicio**

Edit `ordenes/models.py` — agregar campo:
```python
horas_cobradas = models.DecimalField(
    max_digits=8, decimal_places=2, null=True, blank=True,
    verbose_name="Horas cobradas",
    help_text="Horas cobradas al cliente por este servicio"
)
```

Agregar imports al inicio:
```python
from django.db.models import Sum, F
from cotizaciones.models import Configuracion
```

Agregar propiedades:
```python
@property
def costo_repuestos(self):
    total = self.repuestousado_set.aggregate(
        total=Sum(F('cantidad') * F('precio_unitario'))
    )['total']
    return total or 0

@property
def costo_horas(self):
    horas = self.horas_cobradas or 0
    return horas * Configuracion.get_solo().costo_hora

@property
def margen(self):
    cot = self.cotizacion_set.filter(estado='aprobada').first()
    if not cot:
        return None
    return cot.total - (self.costo_repuestos + self.costo_horas)
```

- [ ] **Step 3: Crear migraciones**

Run:
```bash
python manage.py makemigrations cotizaciones ordenes
python manage.py migrate
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: agrega costo_hora a Configuracion y horas_cobradas + margen a OrdenServicio"
```

---

### Task 2: Dashboard ejecutivo con Chart.js

**Files:**
- Modify: `dashboard/views.py`
- Modify: `dashboard/templates/dashboard/dashboard.html`
- Modify: `dashboard/urls.py`
- Create: `dashboard/templates/dashboard/base_dashboard.html` (opcional, o extender admin base)

- [ ] **Step 1: Actualizar dashboard/views.py**

```python
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta, date
from cotizaciones.models import Cotizacion, ItemCotizacion
from ordenes.models import OrdenServicio
from inventario.models import Producto
import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

@staff_member_required
def dashboard(request):
    now = date.today()
    first_of_month = now.replace(day=1)
    
    # KPIs
    cotizaciones_activas = Cotizacion.objects.filter(
        estado__in=['enviada', 'aprobada'],
        fecha__month=now.month, fecha__year=now.year
    ).count()
    
    tickets_abiertos = OrdenServicio.objects.filter(
        estado__in=['pendiente', 'en_curso']
    ).count()
    
    ingresos_mes = Cotizacion.objects.filter(
        estado='aprobada',
        fecha__month=now.month, fecha__year=now.year
    ).aggregate(total=Sum('total'))['total'] or 0
    
    # Ingresos mensuales (12 meses)
    meses = []
    ingresos_data = []
    for i in range(11, -1, -1):
        m = now.month - i
        y = now.year
        while m < 1:
            m += 12
            y -= 1
        label = datetime(y, m, 1).strftime('%b %Y')
        meses.append(label)
        total = Cotizacion.objects.filter(
            estado='aprobada',
            fecha__month=m, fecha__year=y
        ).aggregate(t=Sum('total'))['t'] or 0
        ingresos_data.append(float(total))
    
    # Cotizaciones por estado
    estados = ['borrador', 'enviada', 'aprobada', 'rechazada', 'anulada']
    estados_data = []
    estados_labels = []
    for e in estados:
        c = Cotizacion.objects.filter(estado=e).count()
        if c > 0:
            estados_labels.append(e.capitalize())
            estados_data.append(c)
    
    # Tickets por técnico
    tecnicos = OrdenServicio.objects.values('tecnico').annotate(
        abiertos=Count('id', filter=Q(estado__in=['pendiente', 'en_curso'])),
        cerrados=Count('id', filter=Q(estado__in=['completado', 'facturado']))
    ).exclude(tecnico__isnull=True).exclude(tecnico='')[:10]
    
    tecnicos_labels = [t['tecnico'] for t in tecnicos]
    tecnicos_abiertos = [t['abiertos'] for t in tecnicos]
    tecnicos_cerrados = [t['cerrados'] for t in tecnicos]
    
    # Top productos
    top_items = ItemCotizacion.objects.values('descripcion').annotate(
        total_cant=Sum('cantidad')
    ).order_by('-total_cant')[:10]
    
    top_prod_labels = [t['descripcion'][:30] for t in top_items]
    top_prod_data = [float(t['total_cant']) for t in top_items]
    
    # Alertas
    alertas = []
    
    # Cotizaciones por vencer
    prox_vencer = Cotizacion.objects.filter(
        estado='enviada',
        valida_hasta__gte=now,
        valida_hasta__lte=now + timedelta(days=7)
    )
    for c in prox_vencer:
        dias = (c.valida_hasta - now).days
        alertas.append({
            'tipo': 'vencimiento',
            'gravedad': 'alta' if dias <= 3 else 'media',
            'mensaje': f"Cotización N°{c.numero:05d} vence en {dias} día(s) — {c.cliente.razon_social}",
            'url': f'/admin/cotizaciones/cotizacion/{c.pk}/change/'
        })
    
    # Garantías por vencer
    prox_garantia = OrdenServicio.objects.filter(
        garantia_fin__gte=now,
        garantia_fin__lte=now + timedelta(days=30),
        estado__in=['completado', 'facturado']
    )
    for o in prox_garantia:
        dias = (o.garantia_fin - now).days
        alertas.append({
            'tipo': 'garantia',
            'gravedad': 'media',
            'mensaje': f"TKT {o.codigo_seguimiento} — garantía vence en {dias} día(s) — {o.cliente.razon_social}",
            'url': f'/admin/ordenes/ordenservicio/{o.pk}/change/'
        })
    
    # Stock crítico
    stock_bajo = Producto.objects.filter(stock_actual__lte=models.F('stock_minimo'))
    for p in stock_bajo:
        alertas.append({
            'tipo': 'stock',
            'gravedad': 'alta' if p.stock_actual == 0 else 'media',
            'mensaje': f"Stock bajo: {p.nombre} ({p.stock_actual}/{p.stock_minimo})",
            'url': f'/admin/inventario/producto/{p.pk}/change/'
        })
    
    # Tickets inactivos
    inactivos = OrdenServicio.objects.filter(
        estado__in=['pendiente', 'en_curso'],
        updated_at__lte=now - timedelta(days=7)
    )
    for o in inactivos:
        alertas.append({
            'tipo': 'inactivo',
            'gravedad': 'media',
            'mensaje': f"TKT {o.codigo_seguimiento} sin movimiento desde {o.updated_at.strftime('%d/%m')} — {o.cliente.razon_social}",
            'url': f'/admin/ordenes/ordenservicio/{o.pk}/change/'
        })
    
    # Últimas cotizaciones
    ultimas_cot = Cotizacion.objects.select_related('cliente').order_by('-created_at')[:10]
    ultimos_tickets = OrdenServicio.objects.select_related('cliente').order_by('-created_at')[:10]
    
    context = {
        'cotizaciones_activas': cotizaciones_activas,
        'tickets_abiertos': tickets_abiertos,
        'ingresos_mes': int(ingresos_mes),
        'mes_labels': json.dumps(meses),
        'ingresos_data': json.dumps(ingresos_data),
        'estados_labels': json.dumps(estados_labels),
        'estados_data': json.dumps(estados_data),
        'tecnicos_labels': json.dumps(tecnicos_labels),
        'tecnicos_abiertos': json.dumps(tecnicos_abiertos),
        'tecnicos_cerrados': json.dumps(tecnicos_cerrados),
        'top_prod_labels': json.dumps(top_prod_labels),
        'top_prod_data': json.dumps(top_prod_data),
        'alertas': sorted(alertas, key=lambda a: {'alta': 0, 'media': 1, 'baja': 2}[a['gravedad']]),
        'ultimas_cotizaciones': ultimas_cot,
        'ultimos_tickets': ultimos_tickets,
    }
    return render(request, 'dashboard/dashboard.html', context)
```

- [ ] **Step 2: Actualizar template dashboard.html**

```html
{% extends "admin/base_site.html" %}
{% load static %}

{% block title %}Dashboard {{ block.super }}{% endblock %}

{% block extrastyle %}
{{ block.super }}
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
.dash-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
.dash-card { background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid #2c5282; }
.dash-card .num { font-size: 28px; font-weight: 800; color: #1a365d; }
.dash-card .label { font-size: 11px; text-transform: uppercase; color: #718096; font-weight: 600; letter-spacing: 0.5px; }
.dash-card.ingresos { border-left-color: #38a169; }
.dash-card.tickets { border-left-color: #e53e3e; }
.dash-card.cotizaciones { border-left-color: #2c5282; }
.charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 16px; margin-bottom: 24px; }
.chart-card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.chart-card h3 { font-size: 13px; margin: 0 0 12px; color: #2d3748; }
.alertas-list { margin-bottom: 24px; }
.alerta { padding: 10px 14px; margin-bottom: 6px; border-radius: 6px; font-size: 13px; display: flex; align-items: center; gap: 10px; }
.alerta a { color: inherit; text-decoration: underline; }
.alerta.alta { background: #fed7d7; color: #c53030; border-left: 4px solid #e53e3e; }
.alerta.media { background: #fefcbf; color: #975a16; border-left: 4px solid #d69e2e; }
.alerta.baja { background: #bee3f8; color: #2a4365; border-left: 4px solid #3182ce; }
.alerta .badge { font-size: 10px; font-weight: 700; text-transform: uppercase; padding: 2px 6px; border-radius: 3px; }
.alerta.alta .badge { background: #e53e3e; color: #fff; }
.alerta.media .badge { background: #d69e2e; color: #fff; }
.tablas-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.tabla-card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.tabla-card h3 { font-size: 13px; margin: 0 0 8px; color: #2d3748; }
.tabla-card table { width: 100%; border-collapse: collapse; font-size: 12px; }
.tabla-card td, .tabla-card th { padding: 6px 8px; border-bottom: 1px solid #edf2f7; text-align: left; }
.tabla-card th { font-weight: 600; color: #718096; font-size: 10px; text-transform: uppercase; }
</style>
{% endblock %}

{% block content %}
<div id="content-main">
    <h1 style="margin-top:0;">Dashboard Ejecutivo</h1>

    <!-- KPIs -->
    <div class="dash-grid">
        <div class="dash-card cotizaciones">
            <div class="label">Cotizaciones Activas (Mes)</div>
            <div class="num">{{ cotizaciones_activas }}</div>
        </div>
        <div class="dash-card tickets">
            <div class="label">Tickets Abiertos</div>
            <div class="num">{{ tickets_abiertos }}</div>
        </div>
        <div class="dash-card ingresos">
            <div class="label">Ingresos del Mes</div>
            <div class="num">${{ ingresos_mes|floatformat:0 }}</div>
        </div>
    </div>

    <!-- Alertas -->
    {% if alertas %}
    <div class="alertas-list">
        <h2 style="font-size:14px; margin-bottom:8px;">Alertas</h2>
        {% for a in alertas %}
        <div class="alerta {{ a.gravedad }}">
            <span class="badge">{{ a.tipo }}</span>
            <a href="{{ a.url }}" target="_blank">{{ a.mensaje }}</a>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    <!-- Gráficos -->
    <div class="charts-grid">
        <div class="chart-card">
            <h3>Ingresos Mensuales</h3>
            <canvas id="chartIngresos" height="200"></canvas>
        </div>
        <div class="chart-card">
            <h3>Cotizaciones por Estado</h3>
            <canvas id="chartEstados" height="200"></canvas>
        </div>
        <div class="chart-card">
            <h3>Tickets por Técnico</h3>
            <canvas id="chartTecnicos" height="200"></canvas>
        </div>
        <div class="chart-card">
            <h3>Top Productos/Servicios</h3>
            <canvas id="chartProductos" height="200"></canvas>
        </div>
    </div>

    <!-- Tablas -->
    <div class="tablas-grid">
        <div class="tabla-card">
            <h3>Últimas Cotizaciones</h3>
            <table>
                <tr><th>N°</th><th>Cliente</th><th>Total</th><th>Estado</th><th>Fecha</th></tr>
                {% for c in ultimas_cotizaciones %}
                <tr>
                    <td><a href="/admin/cotizaciones/cotizacion/{{ c.pk }}/change/">{{ c.numero|stringformat:"05d" }}</a></td>
                    <td>{{ c.cliente.razon_social|truncatechars:25 }}</td>
                    <td>${{ c.total|floatformat:0 }}</td>
                    <td>{{ c.estado }}</td>
                    <td>{{ c.fecha|date:"d/m/Y" }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        <div class="tabla-card">
            <h3>Últimos Tickets</h3>
            <table>
                <tr><th>Código</th><th>Cliente</th><th>Estado</th><th>Técnico</th><th>Actualización</th></tr>
                {% for t in ultimos_tickets %}
                <tr>
                    <td><a href="/admin/ordenes/ordenservicio/{{ t.pk }}/change/">{{ t.codigo_seguimiento }}</a></td>
                    <td>{{ t.cliente.razon_social|truncatechars:25 }}</td>
                    <td>{{ t.estado }}</td>
                    <td>{{ t.tecnico|default:"-" }}</td>
                    <td>{{ t.updated_at|date:"d/m/Y" }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
</div>

<script>
const chartColors = { blue: '#2c5282', green: '#38a169', red: '#e53e3e', yellow: '#d69e2e', purple: '#805ad5' };

new Chart(document.getElementById('chartIngresos'), {
    type: 'line',
    data: {
        labels: {{ mes_labels|safe }},
        datasets: [{ label: 'Ingresos ($)', data: {{ ingresos_data|safe }}, borderColor: chartColors.blue, backgroundColor: 'rgba(44,82,130,0.1)', fill: true, tension: 0.3 }]
    },
    options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { callback: v => '$' + v.toLocaleString('es-CL') } } } }
});

new Chart(document.getElementById('chartEstados'), {
    type: 'doughnut',
    data: {
        labels: {{ estados_labels|safe }},
        datasets: [{ data: {{ estados_data|safe }}, backgroundColor: ['#2c5282','#d69e2e','#38a169','#e53e3e','#a0aec0'] }]
    },
    options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
});

new Chart(document.getElementById('chartTecnicos'), {
    type: 'bar',
    data: {
        labels: {{ tecnicos_labels|safe }},
        datasets: [
            { label: 'Abiertos', data: {{ tecnicos_abiertos|safe }}, backgroundColor: chartColors.red },
            { label: 'Cerrados', data: {{ tecnicos_cerrados|safe }}, backgroundColor: chartColors.green }
        ]
    },
    options: { responsive: true, scales: { y: { beginAtZero: true, stacked: false } } }
});

new Chart(document.getElementById('chartProductos'), {
    type: 'bar',
    data: {
        labels: {{ top_prod_labels|safe }},
        datasets: [{ label: 'Cantidad', data: {{ top_prod_data|safe }}, backgroundColor: chartColors.purple }]
    },
    options: { indexAxis: 'y', responsive: true, plugins: { legend: { display: false } }, scales: { x: { beginAtZero: true } } }
});
</script>
{% endblock %}
```

- [ ] **Step 3: Verificar que dashboard/urls.py tenga la ruta**

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: dashboard ejecutivo con Chart.js y panel de alertas"
```

---

### Task 3: Reportes financieros

**Files:**
- Create: `dashboard/templates/dashboard/reportes.html`
- Modify: `dashboard/views.py` (agregar vista reportes)
- Modify: `dashboard/urls.py` (agregar ruta)

- [ ] **Step 1: Agregar vista reportes en dashboard/views.py**

```python
@staff_member_required
def reportes(request):
    from cotizaciones.models import Configuracion
    from django.db.models import Sum, F, Value
    from django.db.models.functions import Coalesce
    
    now = date.today()
    costo_hora = Configuracion.get_solo().costo_hora
    
    # Filtros
    mes = request.GET.get('mes', str(now.month))
    ano = request.GET.get('ano', str(now.year))
    tecnico_filtro = request.GET.get('tecnico', '')
    
    # Obtener todas las órdenes completadas/facturadas que tienen cotización aprobada
    ordenes = OrdenServicio.objects.filter(
        estado__in=['completado', 'facturado'],
        cotizacion__estado='aprobada'
    ).select_related('cliente').prefetch_related('repuestousado_set', 'cotizacion_set')
    
    if mes and mes != 'all':
        ordenes = ordenes.filter(fecha_termino__month=int(mes), fecha_termino__year=int(ano))
    if tecnico_filtro:
        ordenes = ordenes.filter(tecnico=tecnico_filtro)
    
    datos = []
    total_ingresos = 0
    total_costos = 0
    total_margen = 0
    
    for o in ordenes:
        cot = o.cotizacion_set.filter(estado='aprobada').first()
        if not cot:
            continue
        ingreso = float(cot.total)
        costo_rep = float(o.costo_repuestos)
        costo_h = float(o.horas_cobradas or 0) * float(costo_hora)
        costo_total = costo_rep + costo_h
        margen = ingreso - costo_total
        porc_margen = (margen / ingreso * 100) if ingreso > 0 else 0
        
        total_ingresos += ingreso
        total_costos += costo_total
        total_margen += margen
        
        datos.append({
            'codigo': o.codigo_seguimiento,
            'cliente': o.cliente.razon_social,
            'tecnico': o.tecnico or '-',
            'fecha': o.fecha_termino or o.fecha_ingreso,
            'ingreso': ingreso,
            'costo_repuestos': costo_rep,
            'horas': float(o.horas_cobradas or 0),
            'costo_horas': costo_h,
            'costo_total': costo_total,
            'margen': margen,
            'porc_margen': porc_margen,
        })
    
    # Técnicos disponibles para filtro
    tecnicos = OrdenServicio.objects.exclude(
        tecnico__isnull=True
    ).exclude(tecnico='').values_list('tecnico', flat=True).distinct().order_by('tecnico')
    
    # Meses
    meses_opts = [
        ('1','Enero'),('2','Febrero'),('3','Marzo'),('4','Abril'),
        ('5','Mayo'),('6','Junio'),('7','Julio'),('8','Agosto'),
        ('9','Septiembre'),('10','Octubre'),('11','Noviembre'),('12','Diciembre')
    ]
    
    context = {
        'datos': datos,
        'total_ingresos': total_ingresos,
        'total_costos': total_costos,
        'total_margen': total_margen,
        'porc_margen_total': (total_margen / total_ingresos * 100) if total_ingresos > 0 else 0,
        'mes_actual': mes,
        'ano_actual': ano,
        'tecnico_filtro': tecnico_filtro,
        'tecnicos': tecnicos,
        'meses_opts': meses_opts,
    }
    return render(request, 'dashboard/reportes.html', context)
```

- [ ] **Step 2: Agregar ruta en dashboard/urls.py**

```python
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('reportes/', views.reportes, name='dashboard_reportes'),
]
```

- [ ] **Step 3: Crear template dashboard/reportes.html**

```html
{% extends "admin/base_site.html" %}
{% load static %}

{% block title %}Reportes Financieros{% endblock %}

{% block extrastyle %}
{{ block.super }}
<style>
.report-filters { background: #fff; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 16px; display: flex; gap: 12px; align-items: end; flex-wrap: wrap; }
.report-filters label { font-size: 11px; font-weight: 600; text-transform: uppercase; color: #718096; display: block; margin-bottom: 4px; }
.report-filters select, .report-filters button { padding: 6px 12px; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 13px; }
.report-filters button { background: #2c5282; color: #fff; border: none; cursor: pointer; font-weight: 600; }
.resumen-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 16px; }
.resumen-card { background: #fff; padding: 14px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
.resumen-card .num { font-size: 22px; font-weight: 800; }
.resumen-card .label { font-size: 10px; text-transform: uppercase; color: #718096; font-weight: 600; }
table.report-table { width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; font-size: 12px; }
table.report-table th { background: #2c5282; color: #fff; padding: 8px 10px; text-align: left; font-size: 10px; text-transform: uppercase; }
table.report-table td { padding: 6px 10px; border-bottom: 1px solid #edf2f7; }
table.report-table tr:nth-child(even) td { background: #f7fafc; }
.tr { text-align: right; }
</style>
{% endblock %}

{% block content %}
<div id="content-main">
    <h1>Reportes Financieros</h1>

    <form class="report-filters" method="GET">
        <div>
            <label>Mes</label>
            <select name="mes">
                <option value="all">Todos</option>
                {% for v, n in meses_opts %}
                <option value="{{ v }}" {% if mes_actual == v %}selected{% endif %}>{{ n }}</option>
                {% endfor %}
            </select>
        </div>
        <div>
            <label>Año</label>
            <input type="number" name="ano" value="{{ ano_actual }}" style="width:80px;">
        </div>
        <div>
            <label>Técnico</label>
            <select name="tecnico">
                <option value="">Todos</option>
                {% for t in tecnicos %}
                <option value="{{ t }}" {% if tecnico_filtro == t %}selected{% endif %}>{{ t }}</option>
                {% endfor %}
            </select>
        </div>
        <div>
            <button type="submit">Filtrar</button>
        </div>
    </form>

    {% if datos %}
    <div class="resumen-grid">
        <div class="resumen-card">
            <div class="label">Ingresos Totales</div>
            <div class="num" style="color:#38a169;">${{ total_ingresos|floatformat:0 }}</div>
        </div>
        <div class="resumen-card">
            <div class="label">Costos Totales</div>
            <div class="num" style="color:#e53e3e;">${{ total_costos|floatformat:0 }}</div>
        </div>
        <div class="resumen-card">
            <div class="label">Margen Total</div>
            <div class="num" style="color:#2c5282;">${{ total_margen|floatformat:0 }}</div>
        </div>
        <div class="resumen-card">
            <div class="label">% Margen Promedio</div>
            <div class="num">{{ porc_margen_total|floatformat:1 }}%</div>
        </div>
    </div>

    <table class="report-table">
        <tr>
            <th>Ticket</th>
            <th>Cliente</th>
            <th>Técnico</th>
            <th>Fecha</th>
            <th class="tr">Ingreso</th>
            <th class="tr">Costo Rep.</th>
            <th>Horas</th>
            <th class="tr">Costo Horas</th>
            <th class="tr">Costo Total</th>
            <th class="tr">Margen</th>
            <th class="tr">% Margen</th>
        </tr>
        {% for d in datos %}
        <tr>
            <td>{{ d.codigo }}</td>
            <td>{{ d.cliente }}</td>
            <td>{{ d.tecnico }}</td>
            <td>{{ d.fecha|date:"d/m/Y" }}</td>
            <td class="tr">${{ d.ingreso|floatformat:0 }}</td>
            <td class="tr">${{ d.costo_repuestos|floatformat:0 }}</td>
            <td>{{ d.horas|floatformat:1 }}</td>
            <td class="tr">${{ d.costo_horas|floatformat:0 }}</td>
            <td class="tr">${{ d.costo_total|floatformat:0 }}</td>
            <td class="tr" style="color:{% if d.margen >= 0 %}#38a169{% else %}#e53e3e{% endif %};">${{ d.margen|floatformat:0 }}</td>
            <td class="tr">{{ d.porc_margen|floatformat:1 }}%</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p style="text-align:center; padding:40px; color:#a0aec0;">No hay datos para los filtros seleccionados. Asegúrate de que existan órdenes completadas con cotizaciones aprobadas.</p>
    {% endif %}
</div>
{% endblock %}
```

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "feat: reportes financieros con margen por orden de servicio"
```

---

### Task 4: Management commands para recordatorios automáticos

**Files:**
- Create: `ordenes/management/commands/check_cotizaciones.py`
- Create: `ordenes/management/commands/check_garantias.py`
- Create: `ordenes/management/commands/check_stock.py`
- Create: `ordenes/management/commands/check_tickets_inactivos.py`

- [ ] **Step 1: Crear ordenes/management/commands/check_cotizaciones.py**

```python
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from datetime import date, timedelta
from cotizaciones.models import Cotizacion, Configuracion

class Command(BaseCommand):
    help = "Envía alerta de cotizaciones próximas a vencer"

    def handle(self, *args, **options):
        config = Configuracion.get_solo()
        now = date.today()
        prox = Cotizacion.objects.filter(
            estado='enviada',
            valida_hasta__gte=now,
            valida_hasta__lte=now + timedelta(days=3)
        ).select_related('cliente')

        if not prox.exists():
            self.stdout.write("Sin cotizaciones por vencer")
            return

        items = [f"N°{c.numero:05d} - {c.cliente.razon_social} - ${c.total:,.0f} - Vence: {c.valida_hasta}" for c in prox]
        cuerpo = "Cotizaciones próximas a vencer:\n\n" + "\n".join(items)

        send_mail(
            subject=f"[CACD] {prox.count()} cotización(es) por vencer",
            message=cuerpo,
            from_email=config.email,
            recipient_list=[config.email],
            fail_silently=True,
        )
        self.stdout.write(f"Alerta enviada: {prox.count()} cotizaciones por vencer")
```

- [ ] **Step 2: Crear ordenes/management/commands/check_garantias.py**

```python
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from datetime import date, timedelta
from ordenes.models import OrdenServicio
from cotizaciones.models import Configuracion

class Command(BaseCommand):
    help = "Envía alerta de garantías próximas a vencer"

    def handle(self, *args, **options):
        config = Configuracion.get_solo()
        now = date.today()
        prox = OrdenServicio.objects.filter(
            garantia_fin__gte=now,
            garantia_fin__lte=now + timedelta(days=7),
            estado__in=['completado', 'facturado']
        ).select_related('cliente')

        if not prox.exists():
            self.stdout.write("Sin garantías por vencer")
            return

        items = [f"TKT {o.codigo_seguimiento} - {o.cliente.razon_social} - Vence: {o.garantia_fin}" for o in prox]
        cuerpo = "Garantías próximas a vencer:\n\n" + "\n".join(items)

        send_mail(
            subject=f"[CACD] {prox.count()} garantía(s) por vencer",
            message=cuerpo,
            from_email=config.email,
            recipient_list=[config.email],
            fail_silently=True,
        )
        self.stdout.write(f"Alerta enviada: {prox.count()} garantías por vencer")
```

- [ ] **Step 3: Crear ordenes/management/commands/check_stock.py**

```python
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.db.models import F
from inventario.models import Producto
from cotizaciones.models import Configuracion

class Command(BaseCommand):
    help = "Envía alerta de productos con stock crítico"

    def handle(self, *args, **options):
        config = Configuracion.get_solo()
        bajo = Producto.objects.filter(stock_actual__lte=F('stock_minimo'))

        if not bajo.exists():
            self.stdout.write("Stock normal")
            return

        items = [f"{p.sku} - {p.nombre}: {p.stock_actual}/{p.stock_minimo}" for p in bajo]
        cuerpo = "Productos con stock crítico:\n\n" + "\n".join(items)

        send_mail(
            subject=f"[CACD] {bajo.count()} producto(s) con stock crítico",
            message=cuerpo,
            from_email=config.email,
            recipient_list=[config.email],
            fail_silently=True,
        )
        self.stdout.write(f"Alerta enviada: {bajo.count()} productos con stock bajo")
```

- [ ] **Step 4: Crear ordenes/management/commands/check_tickets_inactivos.py**

```python
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from datetime import date, timedelta
from ordenes.models import OrdenServicio
from cotizaciones.models import Configuracion

class Command(BaseCommand):
    help = "Envía alerta de tickets sin movimiento"

    def handle(self, *args, **options):
        config = Configuracion.get_solo()
        now = date.today()
        inactivos = OrdenServicio.objects.filter(
            estado__in=['pendiente', 'en_curso'],
            updated_at__lte=now - timedelta(days=7)
        ).select_related('cliente')

        if not inactivos.exists():
            self.stdout.write("Sin tickets inactivos")
            return

        items = [f"TKT {o.codigo_seguimiento} - {o.cliente.razon_social} - Técnico: {o.tecnico or '-'} - Último: {o.updated_at.strftime('%d/%m')}" for o in inactivos]
        cuerpo = "Tickets sin movimiento en más de 7 días:\n\n" + "\n".join(items)

        send_mail(
            subject=f"[CACD] {inactivos.count()} ticket(s) inactivos",
            message=cuerpo,
            from_email=config.email,
            recipient_list=[config.email],
            fail_silently=True,
        )
        self.stdout.write(f"Alerta enviada: {inactivos.count()} tickets inactivos")
```

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: management commands para recordatorios automáticos"
```
