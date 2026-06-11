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

    ordenes_mes = OrdenServicio.objects.filter(fecha_ingreso__gte=month_start)
    completadas_mes = ordenes_mes.filter(estado='completado')
    horas_mes = sum(o.horas_trabajadas for o in completadas_mes if o.horas_trabajadas)

    pendientes = OrdenServicio.objects.filter(estado='pendiente').count()
    en_curso = OrdenServicio.objects.filter(estado='en_curso').count()

    cotizaciones_pendientes = Cotizacion.objects.filter(estado__in=['borrador', 'enviada']).count()

    garantias_proximas = OrdenServicio.objects.filter(
        garantia_fin__gte=today, garantia_fin__lte=today + datetime.timedelta(days=30)
    ).count()

    stock_bajo = Producto.objects.filter(stock_actual__lte=models.F('stock_minimo')).count()

    ultimas_ordenes = OrdenServicio.objects.order_by('-fecha_ingreso')[:5]

    context = {
        'ordenes_mes': ordenes_mes.count(),
        'completadas_mes': completadas_mes.count(),
        'horas_mes': horas_mes,
        'pendientes': pendientes,
        'en_curso': en_curso,
        'cotizaciones_pendientes': cotizaciones_pendientes,
        'garantias_proximas': garantias_proximas,
        'stock_bajo': stock_bajo,
        'ultimas_ordenes': ultimas_ordenes,
    }
    return render(request, 'dashboard/dashboard.html', context)
