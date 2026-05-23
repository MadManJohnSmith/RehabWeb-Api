from django.db import models
from django.conf import settings

class Mensaje(models.Model):
    
    # Opciones de estado del mensaje
    ESTADO_CHOICES = [
        ('Enviado', 'Enviado'),
        ('Entregado', 'Entregado'),
        ('Visto', 'Visto'),
    ]

    # Relaciones con el modelo de Usuario (Paciente / Terapeuta)
    remitente = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='mensajes_enviados'
    )
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='mensajes_recibidos'
    )
    
    texto = models.TextField(
        max_length=1000, 
        null=True, 
        blank=True,
        help_text="Texto del mensaje, máximo 1000 caracteres."
    )
    
    imagen = models.ImageField(
        upload_to='chat_images/%Y/%m/', 
        null=True, 
        blank=True,
        help_text="Evidencia fotográfica (PNG/JPG)."
    )

    estado = models.CharField(
        max_length=15, 
        choices=ESTADO_CHOICES, 
        default='Enviado'
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        
        ordering = ['-creado_en']
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'

    def __str__(self):
        return f"De {self.remitente} para {self.destinatario} - {self.creado_en.strftime('%Y-%m-%d %H:%M')}"