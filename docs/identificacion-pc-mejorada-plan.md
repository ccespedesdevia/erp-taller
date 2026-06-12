# Identificación de PC Mejorada — Plan de Implementación

> **For agentic workers:** Steps use checkbox syntax for tracking.

**Goal:** Mejorar el sistema de identificación de PC: tarjeta de descarga en Herramientas, script más completo con informe simplificado, y vista comparativa en admin.

**Architecture:** Feature existente que se extiende. Se modifica `scripts/identificar_pc.py` (más datos + TXT simplificado), se agrega tarjeta en `herramientas.html`, se agrega vista de descarga del script, y se mejora el admin para comparar datos API vs archivo subido.

---

### Tarea 1: Agregar tarjeta "Identificar mi PC" en Herramientas

**Files:**
- Modify: `portal/templates/portal/herramientas.html`

- [ ] **Agregar card de identificación en herramientas.html**

Insertar después del card de Speed Test:

```html
        <!-- Identificación de PC -->
        <div class="card shadow-sm mb-4 border-info">
            <div class="card-header bg-info bg-opacity-10 text-info fw-bold">💻 Identificar mi PC</div>
            <div class="card-body">
                <p>Descarga y ejecuta esta herramienta en el equipo que necesita soporte para que nuestros técnicos puedan identificarlo automáticamente.</p>
                <div class="d-flex gap-2 flex-wrap">
                    <a href="{% url 'descargar_script' %}" class="btn btn-info">
                        ⬇️ Descargar Script
                    </a>
                </div>
                <hr>
                <h6>¿Qué datos se recolectan?</h6>
                <ul class="small mb-2">
                    <li><strong>Hardware:</strong> nombre del equipo, marca, modelo, CPU, RAM, discos, UUID BIOS, MAC</li>
                    <li><strong>Software:</strong> lista de programas instalados</li>
                    <li><strong>Errores:</strong> errores recientes del sistema (solo si se ejecuta como Administrador)</li>
                </ul>
                <p class="small text-muted mb-0">🔒 No se recolectan documentos personales, historial de navegación, ni archivos del usuario.</p>
                <hr>
                <p class="mb-0 small">
                    ¿Ya tienes un ticket?
                    <a href="{% url 'portal_seguir' %}">Ingresa el código aquí</a>
                    para subir el informe generado.
                </p>
            </div>
        </div>
```

### Tarea 2: Vista de descarga del script

**Files:**
- Add: `portal/views.py` — vista `descargar_script`
- Modify: `portal/urls.py` — agregar ruta

- [ ] **Agregar vista de descarga en portal/views.py**

```python
import os
from django.http import FileResponse
from django.conf import settings

def descargar_script(request):
    ruta = os.path.join(settings.BASE_DIR, 'scripts', 'identificar_pc.py')
    return FileResponse(open(ruta, 'rb'), as_attachment=True, filename='CACD_Identificar_PC.py')
```

- [ ] **Agregar ruta en portal/urls.py**

```python
    path('descargar-script/', views.descargar_script, name='descargar_script'),
```

### Tarea 3: Modificar script — más datos

**Files:**
- Modify: `scripts/identificar_pc.py`

- [ ] **Agregar recolección de datos adicionales en info_hardware()**

Agregar después de la línea de `i['disco_tamano']`:

```python
    i['windows_version'] = _cmd(['wmic', 'os', 'get', 'Caption']).splitlines()[-1].strip() if _cmd(['wmic', 'os', 'get', 'Caption']) else ''
    i['arquitectura'] = _cmd(['wmic', 'os', 'get', 'OSArchitecture']).splitlines()[-1].strip() if _cmd(['wmic', 'os', 'get', 'OSArchitecture']) else ''
    i['ultimo_boot'] = _cmd(['wmic', 'os', 'get', 'LastBootUpTime']).splitlines()[-1].strip() if _cmd(['wmic', 'os', 'get', 'LastBootUpTime']) else ''
```

- [ ] **Agregar info de Application event logs en info_errores()**

Modificar la función `info_errores()` para que intente leer también Application logs:

```python
def info_errores():
    errores = []
    for log in ['System', 'Application']:
        raw = _cmd(['wevtutil', 'qe', log, '/q:Event[System[(Level=1 or Level=2)]]', '/c:10', '/f:text'])
        if not raw:
            continue
        evento = {}
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith('Provider'):
                m = re.search(r'Name:\s*(\S+)', line)
                if m:
                    evento['fuente'] = m.group(1)
            elif line.startswith('TimeCreated'):
                m = re.search(r'SystemTime:\s*(\S+)', line)
                if m:
                    evento['fecha'] = m.group(1)
            elif line.startswith('EventId'):
                m = re.search(r'(\d+)', line)
                if m:
                    evento['id'] = m.group(1)
            elif line.startswith('Level'):
                evento['nivel'] = 'Error' if '2' in line else 'Crítico'
            elif line.startswith('Message'):
                m = re.search(r'Message\s*(.*)', line)
                if m and m.group(1).strip():
                    evento['mensaje'] = m.group(1).strip()
            if evento.get('fuente') and evento.get('mensaje'):
                evento['log'] = log
                errores.append(dict(evento))
                evento = {}
    return errores[:20]
```

- [ ] **Agregar top procesos por RAM**

Agregar función `info_procesos()`:

```python
def info_procesos():
    """Top 10 procesos por uso de memoria (no requiere admin)."""
    procesos = []
    raw = _cmd(['tasklist', '/fo', 'csv', '/nh'])
    if not raw:
        return procesos
    lines = raw.splitlines()
    parsed = []
    for line in lines:
        parts = line.split(',')
        if len(parts) >= 5:
            nombre = parts[0].strip('" ')
            try:
                memoria = int(parts[4].strip('" ').replace('.', '').replace(',', ''))
                parsed.append((nombre, memoria))
            except:
                pass
    parsed.sort(key=lambda x: x[1], reverse=True)
    for nombre, memoria in parsed[:10]:
        mb = memoria / 1024
        procesos.append({'nombre': nombre, 'memoria_mb': round(mb, 1)})
    return procesos
```

- [ ] **Actualizar payload en main() para incluir procesos**

```python
    payload['software'] = sw
    payload['errores'] = errs
    payload['procesos'] = procs
```

### Tarea 4: Modificar script — informe TXT simplificado

**Files:**
- Modify: `scripts/identificar_pc.py`

- [ ] **Reemplazar generar_txt() para que muestre solo datos básicos**

```python
def generar_txt(info, ticket_codigo):
    escritorio = os.path.join(os.path.expanduser('~'), 'Desktop')
    if not os.path.exists(escritorio):
        escritorio = os.path.expanduser('~')
    cod = ticket_codigo or 'SIN-TICKET'
    ruta = os.path.join(escritorio, f'INFORME_{cod}.txt')

    with open(ruta, 'w', encoding='utf-8') as f:
        f.write('=== INFORME DE IDENTIFICACION DE PC ===\n')
        f.write(f'Codigo Ticket: {cod}\n')
        f.write(f'Fecha: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}\n')
        f.write(f'{"="*40}\n\n')
        f.write(f'Hostname:    {info.get("hostname", "")}\n')
        f.write(f'Fabricante:  {info.get("fabricante", "")}\n')
        f.write(f'Modelo:      {info.get("modelo_pc", "")}\n')
        f.write(f'Sistema:     {info.get("windows_version", info.get("cpu", ""))}\n')
        f.write(f'UUID BIOS:   {info.get("uuid_bios", "")}\n')
        f.write(f'\n{"="*40}\n')
        f.write('CACD Soluciones - https://ccespedesdevia1715.pythonanywhere.com\n')
        f.write('Este equipo fue identificado correctamente.\n')
    return ruta
```

### Tarea 5: Vista comparativa en admin

**Files:**
- Modify: `ordenes/admin.py`

- [ ] **Reemplazar readonly display de datos_identificacion con tabla comparativa**

Agregar método en `OrdenServicioAdmin`:

```python
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
                import os as os_mod
                ruta = archivo.path
                if os_mod.path.exists(ruta):
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
        lines = content.splitlines()
        for line in lines:
            if ':' in line:
                key, val = line.split(':', 1)
                key = key.strip().lower()
                val = val.strip()
                k = key.replace(' ', '_')
                if 'hostname' in k:
                    d['hostname'] = val
                elif 'fabricante' in k:
                    d['fabricante'] = val
                elif 'modelo' in k and 'pc' not in k:
                    d['modelo_pc'] = val
                elif 'uuid' in k or 'bios' in k:
                    d['uuid_bios'] = val
                elif 'sistema' in k or 'windows' in k:
                    d['windows_version'] = val
        return d

    identificacion_html.short_description = 'Identificación'
```

Y reemplazar en `fieldsets` y `readonly_fields`:

```python
        ('Identificación de PC', {'fields': ['identificacion_html', 'archivo_identificacion']}),
    readonly_fields = ['fecha_ingreso', 'identificacion_html']
```

Además, importar `json` y `format_html` al inicio del archivo:

```python
import json
from django.utils.html import format_html
```

### Tarea 6: Subir cambios

- [ ] **Commit y push a PythonAnywhere**

```bash
git add -A
git commit -m "feat: improved PC identification - download card, more data, simplified report, admin comparison"
git push
```

Luego en PythonAnywhere:
```bash
cd ~/erp-taller && git pull
```
Y Reload web app.
