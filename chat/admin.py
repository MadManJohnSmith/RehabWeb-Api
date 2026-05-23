from django.contrib import admin
from .models import Mensaje

@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ('remitente', 'destinatario', 'creado_en', 'estado')
    list_filter = ('estado', 'creado_en')
    search_fields = ('texto', 'remitente__username', 'destinatario__username')
