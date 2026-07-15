import json
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Q, F
from cotizaciones.models import Cotizacion, ItemCotizacion
from ordenes.models import OrdenServicio
from inventario.models import Producto


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
    prox_vencer = Cotizacion.objects.select_related('cliente').filter(
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
    prox_garantia = OrdenServicio.objects.select_related('cliente').filter(
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
    stock_bajo = Producto.objects.filter(stock_actual__lte=F('stock_minimo'))
    for p in stock_bajo:
        alertas.append({
            'tipo': 'stock',
            'gravedad': 'alta' if p.stock_actual == 0 else 'media',
            'mensaje': f"Stock bajo: {p.nombre} ({p.stock_actual}/{p.stock_minimo})",
            'url': f'/admin/inventario/producto/{p.pk}/change/'
        })

    # Tickets inactivos
    inactivos = OrdenServicio.objects.select_related('cliente').filter(
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


@staff_member_required
def reportes(request):
    from cotizaciones.models import Configuracion

    now = date.today()
    costo_hora = Configuracion.obtener().costo_hora

    mes = request.GET.get('mes', str(now.month))
    ano = request.GET.get('ano', str(now.year))
    tecnico_filtro = request.GET.get('tecnico', '')

    ordenes = OrdenServicio.objects.filter(
        estado__in=['completado', 'facturado'],
        cotizaciones__estado='aprobada'
    ).select_related('cliente').prefetch_related('repuestos', 'cotizaciones')

    if mes and mes != 'all':
        ordenes = ordenes.filter(fecha_termino__month=int(mes), fecha_termino__year=int(ano))
    if tecnico_filtro:
        ordenes = ordenes.filter(tecnico=tecnico_filtro)

    datos = []
    total_ingresos = 0
    total_costos = 0
    total_margen = 0

    for o in ordenes:
        cot = o.cotizaciones.filter(estado='aprobada').first()
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

    tecnicos = OrdenServicio.objects.exclude(
        tecnico__isnull=True
    ).exclude(tecnico='').values_list('tecnico', flat=True).distinct().order_by('tecnico')

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