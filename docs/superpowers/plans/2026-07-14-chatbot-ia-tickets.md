# Chatbot IA para Tickets — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Chatbot con IA en el portal público que guía al cliente a describir su problema y crea el ticket automáticamente.

**Architecture:** Nuevos modelos `ChatSession`/`ChatMessage` en `portal`, servicio `GeminiService` que llama a la API REST de Gemini 1.5 Flash, vistas AJAX para el chat en tiempo real, template con burbujas estilo WhatsApp.

**Tech Stack:** Django 4.x, Gemini 1.5 Flash API (vía `requests`), Google AI Studio API Key

---

### Task 1: Modelos ChatSession y ChatMessage

**Files:**
- Modify: `portal/models.py` (agregar al final)

- [ ] **Step 1: Agregar modelos a portal/models.py**

```python
import uuid
from django.db import models
from django.utils import timezone


class ChatSession(models.Model):
    ESTADOS = [
        ('en_curso', 'En Curso'),
        ('completado', 'Completado'),
        ('ticket_creado', 'Ticket Creado'),
    ]
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=200, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    telefono = models.CharField(max_length=50, blank=True, default='')
    empresa = models.CharField(max_length=200, blank=True, default='')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='en_curso')
    orden_creada = models.ForeignKey(
        'ordenes.OrdenServicio', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='chat_sessions'
    )
    datos_extraidos = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Chat {self.session_id} - {self.estado}'


class ChatMessage(models.Model):
    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name='mensajes'
    )
    role = models.CharField(max_length=20)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'[{self.role}] {self.content[:50]}'
```

- [ ] **Step 2: Crear y aplicar migración**

```bash
python manage.py makemigrations portal
python manage.py migrate portal
```

- [ ] **Step 3: Commit**

```bash
git add portal/models.py portal/migrations/
git commit -m "feat: add ChatSession and ChatMessage models"
```

---

### Task 2: Servicio Gemini (portal/services.py)

**Files:**
- Create: `portal/services.py`

- [ ] **Step 1: Crear portal/services.py**

```python
import json
import requests
from django.conf import settings


SYSTEM_PROMPT = """Eres Sofia, asistente virtual de CACD Soluciones, una empresa de soporte técnico.

Tu trabajo es ayudar a clientes a reportar problemas técnicos conversando naturalmente.

Debes seguir este flujo:
1. Saluda: "¡Hola! Soy Sofia, asistente virtual de CACD Soluciones. ¿En qué puedo ayudarte?"
2. Pregunta nombre completo y datos de contacto (teléfono o email)
3. Pregunta qué equipo tiene problema (tipo: PC/Notebook/Impresora/Otro, marca, modelo)
4. Pregunta qué problema específico tiene
5. Pregunta urgencia (baja/media/alta/urgente)
6. Pregunta empresa (opcional)
7 Cuando tengas toda la información, resume y pregunta: "¿Confirmas que creemos el ticket con estos datos?"
8. Si el usuario confirma, responde SOLO con la palabra CONFIRMAR
9. Si falta información, pídela amablemente

Sé amable, profesional, y conversacional. No des consejos técnicos ni diagnósticos."""
```

- [ ] **Step 2: Agregar la clase GeminiService al mismo archivo**

```python

class GeminiService:
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY

    def _conversacion_a_contents(self, historial, incluir_system=True):
        contents = []
        if incluir_system:
            contents.append({
                'role': 'user',
                'parts': [{'text': SYSTEM_PROMPT}]
            })
            contents.append({
                'role': 'model',
                'parts': [{'text': 'Entendido. Seguiré estas instrucciones.'}]
            })
        for msg in historial:
            role = 'user' if msg.role == 'user' else 'model'
            contents.append({'role': role, 'parts': [{'text': msg.content}]})
        return contents

    def enviar_mensaje(self, historial, mensaje_usuario):
        contents = self._conversacion_a_contents(historial)
        contents.append({'role': 'user', 'parts': [{'text': mensaje_usuario}]})

        payload = {
            'contents': contents,
            'generationConfig': {
                'temperature': 0.7,
                'maxOutputTokens': 512,
                'topK': 40,
                'topP': 0.95,
            },
            'safetySettings': [
                {'category': 'HARM_CATEGORY_HARASSMENT', 'threshold': 'BLOCK_NONE'},
                {'category': 'HARM_CATEGORY_HATE_SPEECH', 'threshold': 'BLOCK_NONE'},
                {'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT', 'threshold': 'BLOCK_NONE'},
                {'category': 'HARM_CATEGORY_DANGEROUS_CONTENT', 'threshold': 'BLOCK_NONE'},
            ],
        }

        resp = requests.post(
            f"{self.API_URL}?key={self.api_key}",
            json=payload,
            timeout=20,
        )

        if resp.status_code == 429:
            raise Exception('Límite de requests alcanzado. Intenta de nuevo en unos segundos.')

        resp.raise_for_status()
        data = resp.json()

        try:
            return data['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            block_reason = data.get('promptFeedback', {}).get('blockReason', 'desconocido')
            raise Exception(f'La IA no pudo responder (razón: {block_reason})')

    def extraer_datos(self, historial):
        contents = self._conversacion_a_contents(historial, incluir_system=False)

        conversacion = "\n".join(
            f"{'Cliente' if m.role == 'user' else 'Sofia'}: {m.content}"
            for m in historial
        )

        contents.append({
            'role': 'user',
            'parts': [{'text': f"""Extrae los datos del cliente y el problema de esta conversación en formato JSON.

{conversacion}

Responde SOLO con JSON:
{{
    "nombre": "",
    "email": "",
    "telefono": "",
    "empresa": "",
    "tipo_equipo": "pc|notebook|impresora|red|otro",
    "marca_equipo": "",
    "modelo_equipo": "",
    "problema": "",
    "urgencia": "baja|media|alta|urgente"
}
Usa valores vacíos si no se mencionaron."""}]
        })

        payload = {
            'contents': contents,
            'generationConfig': {
                'temperature': 0.1,
                'maxOutputTokens': 256,
                'response_mime_type': 'application/json',
            },
        }

        resp = requests.post(
            f"{self.API_URL}?key={self.api_key}",
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        texto = data['candidates'][0]['content']['parts'][0]['text']
        return json.loads(texto)


gemini_service = GeminiService()
```

- [ ] **Step 3: Commit**

```bash
git add portal/services.py
git commit -m "feat: add GeminiService for AI chat"
```

---

### Task 3: Vistas de Chat

**Files:**
- Modify: `portal/views.py` (agregar al final, antes de la última línea en blanco)
- Modify: `portal/urls.py` (agregar rutas)

- [ ] **Step 1: Agregar imports a portal/views.py**

Cambiar la línea `from django.http import FileResponse, HttpResponse` a:
```python
from django.http import FileResponse, HttpResponse, JsonResponse
```

Agregar después de `from cotizaciones.models import Cotizacion`:
```python
import json
from .models import ChatSession, ChatMessage
from .services import gemini_service
```

Agregar al final del archivo:
```python
def chat_inicio(request):
    session = ChatSession.objects.create()
    greeting = gemini_service.enviar_mensaje([], "Inicia la conversación")
    ChatMessage.objects.create(session=session, role='assistant', content=greeting)
    return render(request, 'portal/chat.html', {'session': session})


def chat_ver(request, session_id):
    session = get_object_or_404(ChatSession, pk=session_id)
    return render(request, 'portal/chat.html', {'session': session})


def chat_api(request, session_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    session = get_object_or_404(ChatSession, pk=session_id)
    data = json.loads(request.body)
    mensaje = data.get('mensaje', '').strip()

    if not mensaje:
        return JsonResponse({'error': 'Mensaje vacío'}, status=400)

    if session.mensajes.count() > 100:
        return JsonResponse({'error': 'Límite de mensajes alcanzado.'}, status=400)

    ChatMessage.objects.create(session=session, role='user', content=mensaje)

    try:
        historial = list(session.mensajes.all().order_by('created_at'))
        respuesta = gemini_service.enviar_mensaje(historial[:-1], mensaje)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

    ChatMessage.objects.create(session=session, role='assistant', content=respuesta)

    if respuesta.strip() == 'CONFIRMAR':
        try:
            datos = gemini_service.extraer_datos(historial)
            session.datos_extraidos = datos
            session.nombre = datos.get('nombre', '')
            session.email = datos.get('email', '')
            session.telefono = datos.get('telefono', '')
            session.empresa = datos.get('empresa', '')
            session.save()
            return JsonResponse({'respuesta': respuesta, 'confirmar': True, 'datos': datos})
        except Exception as e:
            return JsonResponse({'respuesta': respuesta, 'confirmar': False, 'error_extraccion': str(e)})

    return JsonResponse({'respuesta': respuesta, 'confirmar': False})


def chat_crear_ticket(request, session_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    session = get_object_or_404(ChatSession, pk=session_id)
    if session.orden_creada:
        return JsonResponse({'codigo': session.orden_creada.codigo_seguimiento})

    datos = session.datos_extraidos
    if not datos:
        return JsonResponse({'error': 'No hay datos para crear el ticket.'}, status=400)

    rut = datos.get('rut', '')
    nombre = datos.get('nombre', 'Cliente sin nombre')
    email = datos.get('email', '')
    telefono = datos.get('telefono', '')
    empresa = datos.get('empresa', '')

    if not rut:
        rut = f'SIN-RUT-{session.session_id.hex[:8].upper()}'

    cliente, _ = Cliente.objects.get_or_create(
        rut=rut,
        defaults={
            'razon_social': empresa or nombre,
            'email': email,
            'telefono': telefono,
        },
    )

    marca = datos.get('marca_equipo', '')
    modelo = datos.get('modelo_equipo', '')
    tipo_equipo = datos.get('tipo_equipo', 'otro')
    equipo = None
    if marca or modelo:
        equipo = Equipo.objects.create(
            cliente=cliente,
            tipo=tipo_equipo if tipo_equipo in dict(Equipo.TIPO_CHOICES) else 'otro',
            marca=marca or 'Sin especificar',
            modelo=modelo or 'Sin especificar',
        )

    problema = datos.get('problema', '')
    urgencia = datos.get('urgencia', 'media')

    orden = OrdenServicio.objects.create(
        cliente=cliente,
        equipo=equipo,
        motivo=problema,
        contacto=nombre,
        telefono=telefono,
        email_contacto=email,
        empresa=empresa,
        estado='pendiente',
    )

    session.orden_creada = orden
    session.estado = 'ticket_creado'
    session.save()

    ComentarioTicket.objects.create(
        orden=orden,
        autor='Sofia (IA)',
        texto=f'Ticket creado vía chat IA.\n\nProblema: {problema}\nUrgencia: {urgencia}\nEquipo: {marca} {modelo}',
        es_tecnico=True,
    )

    return JsonResponse({'codigo': orden.codigo_seguimiento})
```

- [ ] **Step 2: Agregar rutas a portal/urls.py**

```python
    path('chat/', views.chat_inicio, name='portal_chat_inicio'),
    path('chat/<uuid:session_id>/', views.chat_ver, name='portal_chat_ver'),
    path('chat/<uuid:session_id>/api/', views.chat_api, name='portal_chat_api'),
    path('chat/<uuid:session_id>/crear/', views.chat_crear_ticket, name='portal_chat_crear'),
```

- [ ] **Step 3: Commit**

```bash
git add portal/views.py portal/urls.py
git commit -m "feat: add chat views and URLs"
```

---

### Task 4: Template de Chat

**Files:**
- Create: `portal/templates/portal/chat.html`

- [ ] **Step 1: Crear portal/templates/portal/chat.html**

```html
{% load static %}
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat con IA - CACD Soluciones</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; height: 100vh; display: flex; flex-direction: column; }
        .header { background: #1a73e8; color: #fff; padding: 16px 20px; display: flex; align-items: center; gap: 12px; }
        .header a { color: #fff; text-decoration: none; font-size: 20px; }
        .header h1 { font-size: 18px; font-weight: 500; }
        .header .subtitle { font-size: 12px; opacity: 0.85; }
        .chat-container { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 8px; }
        .message { max-width: 80%; padding: 10px 14px; border-radius: 18px; font-size: 14px; line-height: 1.5; word-wrap: break-word; animation: fadeIn 0.3s; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        .message.user { align-self: flex-end; background: #1a73e8; color: #fff; border-bottom-right-radius: 4px; }
        .message.assistant { align-self: flex-start; background: #fff; color: #222; border-bottom-left-radius: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
        .message.system { align-self: center; font-style: italic; color: #666; font-size: 12px; }
        .message .time { font-size: 10px; opacity: 0.6; margin-top: 4px; text-align: right; }
        .typing { align-self: flex-start; background: #fff; color: #222; border-radius: 18px; padding: 12px 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); display: flex; gap: 4px; }
        .typing span { width: 8px; height: 8px; background: #999; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out; }
        .typing span:nth-child(2) { animation-delay: 0.2s; }
        .typing span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
        .input-area { padding: 12px 16px; background: #fff; border-top: 1px solid #e0e0e0; display: flex; gap: 8px; align-items: center; }
        .input-area input { flex: 1; padding: 10px 16px; border: 1px solid #ddd; border-radius: 24px; font-size: 14px; outline: none; }
        .input-area input:focus { border-color: #1a73e8; }
        .input-area button { background: #1a73e8; color: #fff; border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center; }
        .input-area button:disabled { opacity: 0.5; cursor: not-allowed; }
        .confirm-card { background: #fff; border-radius: 12px; padding: 20px; margin: 8px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center; }
        .confirm-card h3 { color: #1a73e8; margin-bottom: 8px; }
        .confirm-card p { color: #555; font-size: 14px; margin-bottom: 4px; }
        .confirm-card .btn { display: inline-block; padding: 10px 24px; border-radius: 24px; border: none; cursor: pointer; font-size: 14px; margin: 8px 4px; }
        .btn-primary { background: #1a73e8; color: #fff; }
        .btn-secondary { background: #e0e0e0; color: #333; }
        .btn-success { background: #34a853; color: #fff; }
        .result-card { text-align: center; padding: 40px 20px; }
        .result-card .codigo { font-size: 32px; font-weight: 700; color: #1a73e8; letter-spacing: 2px; margin: 16px 0; }
        .result-card .links { margin-top: 20px; }
        .result-card .links a { color: #1a73e8; text-decoration: none; margin: 0 12px; font-size: 14px; }
        .error-msg { color: #d93025; font-size: 13px; text-align: center; padding: 8px; }
        @media (max-width: 768px) { .message { max-width: 90%; } }
    </style>
</head>
<body>
    <div class="header">
        <a href="/portal/" title="Volver">&larr;</a>
        <div>
            <h1>Chat CACD Soluciones</h1>
            <div class="subtitle">Asistente virtual Sofia</div>
        </div>
    </div>
    <div class="chat-container" id="chatContainer"></div>
    <div class="input-area" id="inputArea">
        <input type="text" id="mensajeInput" placeholder="Escribe tu mensaje..." autofocus>
        <button id="sendBtn" onclick="enviarMensaje()">&uarr;</button>
    </div>

    <script>
        const sessionId = '{{ session.session_id }}';
        const chatContainer = document.getElementById('chatContainer');
        const mensajeInput = document.getElementById('mensajeInput');
        const sendBtn = document.getElementById('sendBtn');
        const inputArea = document.getElementById('inputArea');

        let esperandoConfirmacion = false;
        let datosTicket = null;

        function addMessage(content, role) {
            const div = document.createElement('div');
            div.className = `message ${role}`;
            const now = new Date();
            const time = now.getHours().toString().padStart(2,'0') + ':' + now.getMinutes().toString().padStart(2,'0');
            div.innerHTML = content.replace(/\n/g, '<br>') + `<div class="time">${time}</div>`;
            chatContainer.appendChild(div);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function showTyping() {
            const div = document.createElement('div');
            div.className = 'typing';
            div.id = 'typingIndicator';
            div.innerHTML = '<span></span><span></span><span></span>';
            chatContainer.appendChild(div);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function hideTyping() {
            const el = document.getElementById('typingIndicator');
            if (el) el.remove();
        }

        async function enviarMensaje() {
            const texto = mensajeInput.value.trim();
            if (!texto || esperandoConfirmacion) return;

            mensajeInput.value = '';
            addMessage(texto, 'user');
            showTyping();
            sendBtn.disabled = true;
            mensajeInput.disabled = true;

            try {
                const resp = await fetch(`/portal/chat/${sessionId}/api/`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-CSRFToken': '{{ csrf_token }}'},
                    body: JSON.stringify({mensaje: texto}),
                });
                const data = await resp.json();

                hideTyping();

                if (data.error) {
                    addMessage('⚠️ ' + data.error, 'system');
                    sendBtn.disabled = false;
                    mensajeInput.disabled = false;
                    return;
                }

                if (data.confirmar) {
                    datosTicket = data.datos;
                    addMessage('He resumido la información. Revisa los datos antes de crear el ticket:', 'assistant');
                    const card = document.createElement('div');
                    card.className = 'confirm-card';
                    let html = '<h3>Resumen del Ticket</h3>';
                    const d = data.datos;
                    html += `<p><strong>Nombre:</strong> ${d.nombre || '—'}</p>`;
                    html += `<p><strong>Contacto:</strong> ${d.email || ''} ${d.telefono ? '| ' + d.telefono : ''}</p>`;
                    html += `<p><strong>Empresa:</strong> ${d.empresa || '—'}</p>`;
                    html += `<p><strong>Equipo:</strong> ${d.marca_equipo || ''} ${d.modelo_equipo || ''} (${d.tipo_equipo || '—'})</p>`;
                    html += `<p><strong>Problema:</strong> ${d.problema || '—'}</p>`;
                    html += `<p><strong>Urgencia:</strong> ${d.urgencia || '—'}</p>`;
                    html += '<div style="margin-top:12px">';
                    html += '<button class="btn btn-primary" onclick="crearTicket()">✅ Crear Ticket</button>';
                    html += '<button class="btn btn-secondary" onclick="cancelarTicket()">✏️ Corregir</button>';
                    html += '</div>';
                    card.innerHTML = html;
                    chatContainer.appendChild(card);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                    esperandoConfirmacion = true;
                    inputArea.style.display = 'none';
                } else {
                    addMessage(data.respuesta, 'assistant');
                }
            } catch (e) {
                hideTyping();
                addMessage('⚠️ Error de conexión. Intenta de nuevo.', 'system');
            }

            sendBtn.disabled = false;
            mensajeInput.disabled = false;
            mensajeInput.focus();
        }

        async function crearTicket() {
            sendBtn.disabled = true;
            showTyping();
            try {
                const resp = await fetch(`/portal/chat/${sessionId}/crear/`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-CSRFToken': '{{ csrf_token }}'},
                });
                const data = await resp.json();
                hideTyping();
                if (data.error) {
                    addMessage('⚠️ Error al crear ticket: ' + data.error, 'system');
                    sendBtn.disabled = false;
                    return;
                }
                chatContainer.innerHTML = '';
                const result = document.createElement('div');
                result.className = 'result-card';
                result.innerHTML = `
                    <h2>✅ Ticket Creado</h2>
                    <p>Tu código de seguimiento es:</p>
                    <div class="codigo">${data.codigo}</div>
                    <div class="links">
                        <a href="/portal/seguir/?codigo=${data.codigo}">🔍 Ver estado</a>
                        <a href="/portal/">🏠 Volver al inicio</a>
                    </div>
                `;
                chatContainer.appendChild(result);
            } catch (e) {
                hideTyping();
                addMessage('⚠️ Error al crear el ticket. Intenta de nuevo.', 'system');
                sendBtn.disabled = false;
            }
        }

        function cancelarTicket() {
            esperandoConfirmacion = false;
            datosTicket = null;
            inputArea.style.display = 'flex';
            const confirmCard = document.querySelector('.confirm-card');
            if (confirmCard) confirmCard.remove();
            addMessage('Cuéntame qué falta o qué corregir.', 'assistant');
            mensajeInput.focus();
        }

        mensajeInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') enviarMensaje();
        });
    </script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add portal/templates/portal/chat.html
git commit -m "feat: add chat template with WhatsApp-style UI"
```

---

### Task 5: Landing Page y Configuración

**Files:**
- Modify: `portal/templates/portal/landing.html` (agregar tarjeta de chat)
- Modify: `erp/settings.py` (agregar GEMINI_API_KEY)
- Modify: `portal/__init__.py` (asegurar que existe)

- [ ] **Step 1: Verificar que portal/__init__.py existe**

```bash
ls -la /tmp/erp-taller/portal/__init__.py
```

Si no existe:
```bash
touch /tmp/erp-taller/portal/__init__.py
```

- [ ] **Step 2: Agregar GEMINI_API_KEY a erp/settings.py**

```python
# Google Gemini API (usar variable de entorno en producción)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
```

Agregar antes de `# Email (desarrollo — en consola)`.

- [ ] **Step 3: Commit**

```bash
git add erp/settings.py
git commit -m "chore: add Gemini API key to settings"
```

---

### Task 6: Probar localmente

- [ ] **Step 1: Verificar sintaxis de Python**

```bash
cd /tmp/erp-taller && python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp.settings')
django.setup()
from portal.models import ChatSession, ChatMessage
print('Models OK')
from portal.services import gemini_service
print('Services OK')
"
```

- [ ] **Step 2: Verificar migraciones**

```bash
cd /tmp/erp-taller && python manage.py makemigrations --check --dry-run
```

- [ ] **Step 3: Ejecutar migraciones pendientes (si las hay)**

```bash
cd /tmp/erp-taller && python manage.py migrate
```

- [ ] **Step 4: Iniciar servidor de prueba y verificar**

```bash
cd /tmp/erp-taller && python manage.py runserver 0.0.0.0:8000 &
sleep 2
curl -s http://localhost:8000/portal/chat/ | head -20
```
