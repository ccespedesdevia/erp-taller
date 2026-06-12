# Identificación de PC — Diseño Mejorado

## Tarjeta en Herramientas
- Nueva tarjeta "Identificar mi PC" en `/portal/herramientas/`
- Botón descargar script, instrucciones, nota privacidad, enlace a subir informe

## Script mejorado
- Más datos: versión exacta Windows, service pack, arquitectura, temperatura discos (si posible), top procesos RAM, Application event logs
- Envía TODO al ERP vía API (invisible)
- Genera INFORME_TKT-XXXXXX.txt en escritorio con solo datos básicos (hostname, fabricante, modelo, Windows, UUID BIOS)

## Vista comparativa en admin
- Sección en detalle del ticket: tabla lado a lado API vs archivo subido
- Verde si coincide, rojo si difiere

## Flujo
1. Ticket simple → técnico acepta → sistema pide identificación
2. Cliente descarga script desde Herramientas
3. Script envía datos al ERP + genera INFORME TXT
4. Cliente sube INFORME desde seguimiento público
5. Admin muestra comparativa
