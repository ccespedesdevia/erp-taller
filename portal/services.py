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
7. Cuando tengas toda la información, resume y pregunta: "¿Confirmas que creemos el ticket con estos datos?"
8. Si el usuario confirma, responde SOLO con la palabra CONFIRMAR
9. Si falta información, pídela amablemente

Sé amable, profesional, y conversacional. No des consejos técnicos ni diagnósticos."""


class GeminiService:
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

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
}}
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
