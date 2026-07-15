# Cotización Redesign — PITAGORA Format + Legal Terms

## Objective
Redesign the Cotización model, admin, and PDF template to match the PITAGORA S.A. format with full Chilean legal terms for IT services, without breaking existing cotizaciones.

## Changes

### 1. Model — Cotizacion (add nullable fields)
- `unidad_negocio` (CharField, blank)
- `moneda` (CharField, default="PESOS CHILE")
- `forma_pago` (CharField, blank)
- `observaciones` (TextField, blank)
- `incluye` (TextField, blank)
- `subtotal` (DecimalField, null/blank)
- `porcentaje_descuento` (DecimalField, default=0)
- `monto_descuento` (DecimalField, default=0)
- `neto` (DecimalField, null/blank)
- `iva` (DecimalField, null/blank)

### 2. Model — ItemCotizacion (add nullable fields)
- `recurso` (CharField, blank) — código del recurso
- `unidad` (CharField, blank) — ej. MES, UNIDAD
- `porcentaje_descuento_item` (DecimalField, default=0)
- `total_item` (DecimalField, null/blank)

### 3. Model — Configuracion (add fields)
- `giro` (CharField, blank) — giro comercial
- `email_recepcion_dte` (EmailField, blank) — email para DTEs
- `terminos_legales` (TextField, blank) — texto completo de términos legales (Chile, servicios TI)

### 4. Admin — CotizacionAdmin
- Update fieldsets: add Unidad de Negocio, Moneda, Forma de Pago, Observaciones, Incluye
- Add totales section: Subtotal, % Dscto, Monto Dscto, Neto, IVA, Total
- Keep all existing fields and behavior intact

### 5. PDF Template (cotizacion_pdf.html)
- Redesign with PITAGORA-style layout:
  - Header: company info (nombre, rut, direccion, giro, fono, email_recepcion) + cotización número + fecha
  - Client info table: Señor(es), Dirección, RUT, Sucursal
  - Business info: Unidad de Negocio, Moneda, Forma de Pago
  - Items table: # — Recurso — Cantidad — Descripción — Unidad — Precio — % Dscto — Total
  - Totals section: Subtotal → % Descuento → Neto → 19% IVA → Total
  - Observaciones + Incluye
  - Términos Legales completos (from Configuracion)
  - Footer

### 6. Legal Terms (stored in Configuracion.terminos_legales)
Full text per conversation with user:
- Validez 15 días
- Valores netos (+19% IVA)
- Pago: 7 días desde facturación (proyectos) / mes anticipado (recurrente)
- Morosidad: interés máximo convencional, suspensión a los 15 días
- Delimitación de alcance
- Responsabilidades del cliente
- Garantía técnica 30 días (pérdida por manipulación de terceros)
- Confidencialidad (Ley 19.628)
- Propiedad intelectual (transferencia contra pago 100%)
- Aceptación: OC o email

## Backward Compatibility
All new fields are nullable/with defaults. Existing cotizaciones remain intact. New cotizaciones can optionally use the new fields.
