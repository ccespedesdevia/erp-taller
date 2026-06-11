import datetime
from django.db import models
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from ordenes.models import OrdenServicio
from cotizaciones.models import Cotizacion
from inventario.models import Producto


@staff_member_required
def dashboard(request):
    today = datetime.date.today()
    month_start = today.replace(day=1)
    week_ago = today - datetime.timedelta(days=7)

    # KPI principales
    total_abiertos = OrdenServicio.objects.filter(estado__in=['pendiente', 'en_curso']).count()
    pendientes = OrdenServicio.objects.filter(estado='pendiente').count()
    en_curso = OrdenServicio.objects.filter(estado='en_curso').count()

    ordenes_mes = OrdenServicio.objects.filter(fecha_ingreso__gte=month_start)
    completadas_mes = ordenes_mes.filter(estado='completado').count()
    facturadas_mes = ordenes_mes.filter(estado='facturado').count()

    # Horas del mes (completadas + facturadas)
    terminadas_mes = ordenes_mes.filter(estado__in=['completado', 'facturado'])
    horas_mes = sum(o.horas_trabajadas for o in terminadas_mes if o.horas_trabajadas)

    # Tiempo promedio de resolución (en días)
    resueltas = OrdenServicio.objects.filter(
        estado__in=['completado', 'facturado'],
        fecha_termino__isnull=False, fecha_ingreso__isnull=False,
    )
    dias_resolucion = 0
    count_resueltas = 0
    for o in resueltas:
        if o.fecha_termino and o.fecha_ingreso:
            dias = (o.fecha_termino - o.fecha_ingreso).days
            dias_resolucion += dias
            count_resueltas += 1
    promedio_dias = round(dias_resolucion / count_resueltas, 1) if count_resueltas else 0

    # Tickets por técnico
    tecnicos = OrdenServicio.objects.exclude(tecnico='').values('tecnico').annotate(
        abiertos=models.Count('id', filter=models.Q(estado__in=['pendiente','en_curso']))
    ).order_by('-abiertos')

    # Últimos 7 días (nuevos tickets)
    nuevos_semana = OrdenServicio.objects.filter(fecha_ingreso__gte=week_ago).count()

    # Garantías próximas
    garantias_proximas = OrdenServicio.objects.filter(
        garantia_fin__gte=today, garantia_fin__lte=today + datetime.timedelta(days=30)
    ).count()

    # Stock bajo
    stock_bajo = Producto.objects.filter(stock_actual__lte=models.F('stock_minimo')).count()

    # Órdenes recientes
    ultimas_ordenes = OrdenServicio.objects.select_related('cliente', 'equipo').order_by('-fecha_ingreso')[:10]

    context = {
        'total_abiertos': total_abiertos,
        'pendientes': pendientes,
        'en_curso': en_curso,
        'ordenes_mes': ordenes_mes.count(),
        'completadas_mes': completadas_mes,
        'facturadas_mes': facturadas_mes,
        'horas_mes': horas_mes,
        'nuevos_semana': nuevos_semana,
        'promedio_dias': promedio_dias,
        'tecnicos': tecnicos,
        'garantias_proximas': garantias_proximas,
        'stock_bajo': stock_bajo,
        'ultimas_ordenes': ultimas_ordenes,
        'hoy': today,
    }
    return render(request, 'dashboard/dashboard.html', context)
