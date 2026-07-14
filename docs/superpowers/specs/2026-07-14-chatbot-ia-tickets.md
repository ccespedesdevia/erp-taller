# AI Chatbot para Creación de Tickets

## Resumen
Chatbot público con IA (Gemini 1.5 Flash) en el portal de CACD Soluciones. Los clientes conversan con la IA para describir su problema y la IA crea el ticket automáticamente.

## Flujo
1. Usuario entra a `/portal/` → hace clic en "Chatear con IA"
2. Chat full-screen se abre con un saludo de la IA
3. Usuario describe su problema naturalmente
4. IA guía: nombre, contacto, equipo, problema, urgencia
5. IA confirma los datos con el usuario
6. Usuario confirma → IA envía JSON estructurado → servidor crea `OrdenServicio`
7. Se muestra código de seguimiento y opción de ver ticket

## Arquitectura

### Modelos (en `portal/models.py`)
- `ChatSession`: UUID, nombre/email/telefono/empresa (recolectados), estado (en_curso|completado|ticket_creado), orden_creada (FK), datos_extraidos (JSON), created_at, updated_at
- `ChatMessage`: session (FK ChatSession), role (user/assistant/system), content, created_at

### Servicio (`portal/services.py`)
- `GeminiService`: wrapper sobre `google-generativeai`
- `enviar_mensaje(historial, mensaje_usuario)` → respuesta texto
- `extraer_datos(historial)` → JSON estructurado via response_mime_type=json
- System prompt define comportamiento (ver abajo)

### Vistas (en `portal/chat_views.py`)
- `chat_inicio(request)` → crea ChatSession, renderiza chat.html
- `chat_api(request, session_id)` → POST AJAX: recibe mensaje, llama Gemini, guarda y devuelve respuesta
- `chat_crear_ticket(request, session_id)` → llama extraer_datos(), crea OrdenServicio, devuelve código

### URLs
- `/portal/chat/` → chat_inicio
- `/portal/chat/<uuid:session_id>/` → chat.html (reanudar)
- `/portal/chat/<uuid:session_id>/api/` → chat_api (POST)
- `/portal/chat/<uuid:session_id]/crear/` → chat_crear_ticket (POST)

### Template
- `portal/templates/portal/chat.html` → chat full-screen con burbujas estilo WhatsApp
- Sin frameworks externos: CSS vanilla + JS fetch para AJAX

## System Prompt
```
Eres Sofia, asistente virtual de CACD Soluciones, empresa de soporte técnico.
Ayudas a clientes a reportar problemas técnicos y creas tickets de servicio.

Debes:
1. Saludar: "¡Hola! Soy Sofia, asistente de CACD Soluciones. ¿En qué puedo ayudarte?"
2. Preguntar nombre completo y datos de contacto (teléfono o email)
3. Preguntar qué equipo tiene problema (marca, modelo, tipo)
4. Preguntar qué problema específico tiene
5. Preguntar urgencia (baja/media/alta/urgente)
6. Preguntar empresa/organización (opcional)
7. Una vez completa la info, resumir todo y preguntar: "¿Confirmas que creemos el ticket con estos datos?"
8. Si confirma, responder SOLO con la palabra CONFIRMAR
9. Si falta algo, pedir especificar

Sé amable y profesional. No des consejos técnicos - solo recolecta info.
```

## Integración Gemini
- API Key en `settings.GEMINI_API_KEY`
- Modelo: `gemini-1.5-flash` (gratuito)
- Llamada POST a `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent`
- `response_mime_type: "application/json"` para extracción estructurada
- Timeout 15s por mensaje

## Consideraciones
- Sin autenticación requerida para iniciar chat
- Rate limiting: 60 req/min gratis en Gemini Flash
- Prevención de spam: máximo 50 mensajes por sesión
- La conversación completa se guarda en BD
- Si Gemini falla, mostrar mensaje amigable
