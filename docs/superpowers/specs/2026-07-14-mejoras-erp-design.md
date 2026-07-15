# Mejoras ERP CACD Soluciones — Especificación

## Objetivo
Implementar 5 mejoras clave: dashboard ejecutivo, reportes financieros con margen, alertas inteligentes, recordatorios automáticos por email, y cálculo de margen real por orden de servicio.

## Arquitectura

### Apps involucradas
- **dashboard/** — Se expande con Chart.js, nuevos templates y vistas para reportes financieros y panel de alertas
- **ordenes/models.py** — Se agregan campos `costo_hora`, `horas_cobradas`, `margen` (propiedad calculada)
- **cotizaciones/models.py** — Se agrega propiedad `margen_estimado` basada en la orden vinculada
- **Management commands** — 4 comandos para recordatorios automáticos

### Modelos nuevos
Ninguno. Toda la lógica se apoya en modelos existentes o propiedades calculadas.

### Modelos modificados
- **Configuracion**: nuevo campo `costo_hora` (DecimalField default 40844.79)
- **OrdenServicio**: nuevo campo `horas_cobradas` (DecimalField, nullable)

### Propiedades calculadas
- `OrdenServicio.margen`: total_cotizacion - (costo_repuestos + horas_cobradas * costo_hora)
- `Cotizacion.margen_estimado`: total - (items_repuestos + orden.horas * costo_hora)

---

## 1. Dashboard Ejecutivo

### Ubicación
- Ruta: `/dashboard/` (ya existe, staff-only)
- Template base: admin (ya usa `templates/admin/base_site.html`)

### Componentes

**KPIs superiores** (4 tarjetas grandes):
- Cotizaciones activas (enviadas + aprobadas este mes)
- Tickets abiertos (pendientes + en_curso)
- Ingresos del mes (suma total cotizaciones aprobadas del mes)
- Margen promedio del mes (promedio márgenes de órdenes completadas)

**Gráficos (Chart.js v4 desde CDN):**
1. **Ingresos mensuales** — gráfico de línea, últimos 12 meses, total cotizaciones aprobadas por mes
2. **Cotizaciones por estado** — gráfico dona: borrador / enviada / aprobada / rechazada / anulada
3. **Tickets por técnico** — gráfico barras, abiertos y cerrados
4. **Top productos/servicios** — gráfico barras horizontal, items más vendidos por cantidad

**Tablas inferiores:**
- Últimas 10 cotizaciones creadas
- Últimos 10 tickets con estado

### Data flow
- Vista `dashboard/views.py` consulta directamente los modelos (sin API REST)
- Los datos se pasan como contexto JSON serializado para Chart.js
- Dashboard se renderiza en el servidor (no SPA)

---

## 2. Reportes Financieros + Margen

### Ubicación
- Nueva ruta: `/dashboard/reportes/`
- Vista: `ReportesView` (staff-only)
- Template: `dashboard/reportes.html`

### Funcionalidad
Tabla con filtros: mes, técnico (FK a OrdenServicio.tecnico, campo raw), cliente

Columnas:
| N° OC | Cliente | Técnico | Fecha | Total Cotización | Costo Repuestos | Horas | Costo Horas | Margen | % Margen |

- **Costo repuestos**: suma de `RepuestoUsado.cantidad * RepuestoUsado.precio_unitario` vinculados a la orden
- **Costo horas**: `OrdenServicio.horas_cobradas * Configuracion.costo_hora`
- **Margen**: `total_cotizacion - (costo_repuestos + costo_horas)`
- **% Margen**: `margen / total_cotizacion * 100`

Exportable a CSV (botón).

---

## 3. Alertas Inteligentes

### Ubicación
Panel embebido en `/dashboard/` (parte del dashboard ejecutivo)

### Tipos de alerta
| Alerta | Query | Destino |
|--------|-------|---------|
| Cotizaciones por vencer | `Cotizacion.objects.filter(valida_hasta__gte=now, valida_hasta__lte=now+7d, estado=enviada)` | Panel + email |
| Garantías por vencer | `OrdenServicio.objects.filter(garantia_fin__gte=now, garantia_fin__lte=now+30d)` | Panel + email |
| Stock crítico | `Producto.objects.filter(stock_actual__lte=F('stock_minimo'))` | Panel + email |
| Tickets inactivos | `OrdenServicio.objects.filter(estado__in=[pendiente,en_curso], updated_at__lte=now-7d)` | Panel + email |
| Cotizaciones sin respuesta | `Cotizacion.objects.filter(estado=enviada, updated_at__lte=now-5d)` | Panel + email |

### Interacción
- Cada alerta se muestra en una tarjeta con color según gravedad (rojo=crítico, amarillo=advertencia, azul=informativo)
- Botón "Desestimar" que oculta la alerta por 24h (opcional v1)
- Click en la alerta navega al admin (ej: click en "Stock crítico" → `/admin/inventario/producto/`)

---

## 4. Recordatorios Automáticos por Email

### Management commands
4 comandos en `ordenes/management/commands/` (ya existe signals.py para email):

| Comando | Frecuencia sugerida | Query | Email |
|---------|-------------------|-------|-------|
| `check_cotizaciones` | Diario | Cotizaciones a 3 días de vencer | Admin (config.email) |
| `check_garantias` | Diario | Garantías a 7 días de vencer | Cliente + Admin |
| `check_stock` | Diario | Productos con stock ≤ mínimo | Admin |
| `check_tickets_inactivos` | Diario | Tickets sin update en 7 días | Técnico asignado |

### Implementación
- Todos heredan de `BaseCommand`
- Usan `django.core.mail.send_mail` (ya configurado SMTP Gmail)
- Se programan via cron en PythonAnywhere (`python manage.py check_cotizaciones`)

### Formato email
- Asunto: "[CACD] Alerta: {tipo} - {detalle}"
- Cuerpo: HTML simple con tabla de items afectados + link al admin

---

## 5. Cálculo de Margen Real

### Modelo

**Configuracion** agrega:
```python
costo_hora = models.DecimalField(max_digits=12, decimal_places=0, default=40845,
    help_text="Costo por hora de servicio en CLP")
```

**OrdenServicio** agrega:
```python
horas_cobradas = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True,
    help_text="Horas cobradas al cliente")
```

**OrdenServicio** propiedad:
```python
@property
def costo_repuestos(self):
    return self.repuestousado_set.aggregate(
        total=Sum(F('cantidad') * F('precio_unitario'))
    )['total'] or 0

@property
def costo_horas(self):
    horas = self.horas_cobradas or 0
    return horas * Configuracion.get_solo().costo_hora

@property
def margen(self):
    # Orden vinculada a cotización aprobada
    cotizacion = self.cotizacion_set.filter(estado='aprobada').first()
    if not cotizacion:
        return None
    return cotizacion.total - (self.costo_repuestos + self.costo_horas)
```

### UI Admin
- Panel de OrdenServicio muestra sección "Margen" con costo repuestos, costo horas y margen calculado (read-only)

---

## Próximos pasos
1. Implementar modelo cambios (migraciones)
2. Dashboard con Chart.js
3. Reportes financieros
4. Alertas en dashboard
5. Management commands para recordatorios
6. Deploy
