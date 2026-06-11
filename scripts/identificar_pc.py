"""
identificar_pc.py — Ejecutar en el PC del cliente para identificarlo en el ERP.
Uso:  python identificar_pc.py  (o compilar a .exe con PyInstaller)
"""

import subprocess
import json
import urllib.request
import urllib.parse
import sys
import os


API_URL = 'https://ccespedesdevia1715.pythonanywhere.com/api/equipos/identificar/'


def ejecutar(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return r.stdout.strip()
    except Exception:
        return ''


def obtener_info():
    info = {}

    # Hostname
    info['hostname'] = ejecutar(['hostname'])

    # UUID de BIOS (identificador único del equipo)
    raw = ejecutar(['wmic', 'csproduct', 'get', 'uuid'])
    for linea in raw.splitlines():
        linea = linea.strip()
        if linea and 'UUID' not in linea:
            info['uuid_bios'] = linea
            break

    # MAC address (primera interfaz física)
    raw = ejecutar(['wmic', 'nic', 'where', 'NetEnabled=TRUE', 'get', 'MACAddress'])
    for linea in raw.splitlines():
        linea = linea.strip()
        if linea and 'MAC' not in linea:
            info['mac_address'] = linea
            break

    # Serial del disco
    raw = ejecutar(['wmic', 'diskdrive', 'get', 'SerialNumber'])
    for linea in raw.splitlines():
        linea = linea.strip()
        if linea and 'Serial' not in linea:
            info['disco_serial'] = linea
            break

    # Serial de la motherboard
    raw = ejecutar(['wmic', 'baseboard', 'get', 'SerialNumber'])
    for linea in raw.splitlines():
        linea = linea.strip()
        if linea and 'Serial' not in linea:
            info['motherboard_serial'] = linea
            break

    return info


def enviar(info):
    data = json.dumps(info).encode()
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode()) if e.code else {'error': str(e)}
    except Exception as e:
        return {'error': str(e)}


def mostrar(resultado):
    if resultado.get('error'):
        print(f'\n  ERROR: {resultado["error"]}')
        return

    print('\n' + '=' * 55)
    print('  CACD Soluciones — Identificación de Equipo')
    print('=' * 55)

    if resultado.get('creado'):
        print('\n  Nuevo equipo registrado en el sistema.')
    else:
        print('\n  Equipo encontrado en nuestros registros.')

    print(f'\n  Tipo:      {resultado.get("tipo", "")}')
    print(f'  Marca:     {resultado.get("marca", "")}')
    print(f'  Modelo:    {resultado.get("modelo", "")}')
    print(f'  N° Serie:  {resultado.get("numero_serie", "")}')

    cliente = resultado.get('cliente')
    if cliente and cliente.get('razon_social'):
        print(f'\n  Cliente:   {cliente["razon_social"]}')
        print(f'  RUT:       {cliente["rut"]}')
        print(f'  ID:        #{cliente["id"]}')

    tickets = resultado.get('tickets', [])
    if tickets:
        print(f'\n  Tickets asociados ({resultado["tickets_count"]}):')
        for t in tickets:
            print(f'    • {t["codigo"]} — {t["estado"]} — {t["fecha"]}')
            if t['motivo']:
                print(f'      Motivo: {t["motivo"][:80]}')
    else:
        print('\n  Sin tickets asociados.')

    print('=' * 55)


def main():
    print('\n  Identificando equipo...')
    info = obtener_info()
    if not any([info.get('uuid_bios'), info.get('mac_address'), info.get('disco_serial')]):
        print('\n  No se pudieron obtener datos del hardware.')
        print('  Ejecutar como Administrador en Windows.')
        input('\n  Presiona Enter para salir...')
        return

    resultado = enviar(info)
    mostrar(resultado)
    input('\n  Presiona Enter para salir...')


if __name__ == '__main__':
    main()
