"""
identificar_pc.py — Identifica el equipo y envía datos al ERP CACD.

INSTRUCCIONES PARA COMPILAR A .exe:
  pip install pyinstaller
  pyinstaller --onefile --noconsole --name CACD_Identificar identificar_pc.py

USO:
  identificar_pc.exe             (sin ventana, solo genera TXT)
  identificar_pc.exe TKT-ABCDEF  (vincula al ticket)

El programa:
  1. Recolecta datos de hardware, software y errores del sistema
  2. Envía los datos al ERP (invisible para el usuario)
  3. Genera INFORME_TKT-XXXXXX.txt en el escritorio
  4. El usuario sube ese TXT al ticket como comprobante
"""

import subprocess, json, urllib.request, os, datetime, sys, re

API_URL = 'https://ccespedesdevia1715.pythonanywhere.com/api/equipos/identificar/'


def _cmd(args):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
        return r.stdout.strip()
    except:
        return ''


def _parse_wmic(raw, field):
    for line in raw.splitlines():
        line = line.strip()
        if line and field.lower() not in line.lower():
            return line
    return ''


def info_hardware():
    i = {}
    i['hostname'] = _cmd(['hostname'])
    i['uuid_bios'] = _parse_wmic(_cmd(['wmic', 'csproduct', 'get', 'uuid']), 'UUID')
    i['mac_address'] = _parse_wmic(_cmd(['wmic', 'nic', 'where', 'NetEnabled=TRUE', 'get', 'MACAddress']), 'MAC')
    i['disco_serial'] = _parse_wmic(_cmd(['wmic', 'diskdrive', 'get', 'SerialNumber']), 'Serial')
    i['motherboard_serial'] = _parse_wmic(_cmd(['wmic', 'baseboard', 'get', 'SerialNumber']), 'Serial')
    i['fabricante'] = _parse_wmic(_cmd(['wmic', 'csproduct', 'get', 'Vendor']), 'Vendor')
    i['modelo_pc'] = _parse_wmic(_cmd(['wmic', 'csproduct', 'get', 'Name']), 'Name')
    i['cpu'] = _parse_wmic(_cmd(['wmic', 'cpu', 'get', 'Name']), 'Name')
    i['ram_gb'] = ''
    raw = _cmd(['wmic', 'computersystem', 'get', 'TotalPhysicalMemory'])
    for l in raw.splitlines():
        l = l.strip()
        if l.isdigit():
            try:
                i['ram_gb'] = f'{int(l) // (1024**3)} GB'
            except:
                pass
            break
    i['disco_modelo'] = _parse_wmic(_cmd(['wmic', 'diskdrive', 'get', 'Model']), 'Model')
    i['disco_tamano'] = ''
    raw = _cmd(['wmic', 'diskdrive', 'get', 'Size'])
    for l in raw.splitlines():
        l = l.strip()
        if l.isdigit():
            try:
                i['disco_tamano'] = f'{int(l) // (1024**3)} GB'
            except:
                pass
            break
    return i


def info_software():
    """Lista de programas instalados (no requiere admin)."""
    programas = []
    raw = _cmd(['wmic', 'product', 'get', 'name,version'])
    for line in raw.splitlines():
        line = line.strip()
        if not line or 'Name' in line:
            continue
        partes = re.split(r'\s{2,}', line, maxsplit=1)
        nombre = partes[0].strip()
        version = partes[1].strip() if len(partes) > 1 else ''
        if nombre:
            programas.append({'nombre': nombre, 'version': version})
    return programas


def info_errores():
    """Errores recientes del sistema (requiere admin, falla silenciosamente si no)."""
    errores = []
    raw = _cmd(['wevtutil', 'qe', 'System', '/q:Event[System[(Level=1 or Level=2)]]', '/c:20', '/f:text'])
    if not raw:
        return errores
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
            errores.append(dict(evento))
            evento = {}
    return errores[:20]


def generar_txt(info, ticket_codigo):
    """Genera INFORME_TKT-XXXXXX.txt en el escritorio."""
    escritorio = os.path.join(os.path.expanduser('~'), 'Desktop')
    if not os.path.exists(escritorio):
        escritorio = os.path.expanduser('~')
    cod = ticket_codigo or 'SIN-TICKET'
    ruta = os.path.join(escritorio, f'INFORME_{cod}.txt')

    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(f'INFORME DE IDENTIFICACION DE EQUIPO\n')
        f.write(f'Codigo: {cod}\n')
        f.write(f'Fecha: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}\n')
        f.write(f'{"="*45}\n\n')
        f.write(f'Hostname:      {info.get("hostname", "")}\n')
        f.write(f'Fabricante:     {info.get("fabricante", "")}\n')
        f.write(f'Modelo:         {info.get("modelo_pc", "")}\n')
        f.write(f'N° Serie PC:    {info.get("uuid_bios", "")}\n')
        f.write(f'CPU:            {info.get("cpu", "")}\n')
        f.write(f'RAM:            {info.get("ram_gb", "")}\n')
        f.write(f'Disco:          {info.get("disco_modelo", "")} ({info.get("disco_tamano", "")})\n')
        f.write(f'MAC:            {info.get("mac_address", "")}\n')
        f.write(f'\n{"="*45}\n')
        f.write('CACD Soluciones — https://ccespedesdevia1715.pythonanywhere.com\n')
    return ruta


def enviar_al_erp(payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        API_URL, data=data,
        headers={'Content-Type': 'application/json'}, method='POST',
    )
    try:
        resp = urllib.request.urlopen(req, timeout=20)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode()
        try:
            return json.loads(cuerpo)
        except:
            return {'error': cuerpo[:200]}
    except Exception as e:
        return {'error': str(e)}


def main():
    ticket_codigo = sys.argv[1].strip().upper() if len(sys.argv) > 1 else ''

    hw = info_hardware()
    sw = info_software()
    errs = info_errores()

    payload = {k: v for k, v in hw.items() if v}
    payload['software'] = sw
    payload['errores'] = errs
    if ticket_codigo:
        payload['ticket_codigo'] = ticket_codigo

    # Enviar al ERP (invisible)
    try:
        resultado = enviar_al_erp(payload)
    except:
        resultado = {}

    # Generar TXT en el escritorio
    txt_path = generar_txt(hw, ticket_codigo)
    # Abrir carpeta para que el usuario vea el archivo
    try:
        subprocess.Popen(['explorer', '/select,', txt_path])
    except:
        pass


if __name__ == '__main__':
    main()
