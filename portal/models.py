import uuid
from django.db import models


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
