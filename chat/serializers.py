from rest_framework import serializers
from .models import Mensaje

class MensajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensaje
        fields = ['id', 'remitente', 'destinatario', 'texto', 'imagen', 'estado', 'creado_en']
        read_only_fields = ['id', 'estado', 'creado_en', 'remitente']

    def validate_texto(self, value):
        #Máximo 1000 caracteres
        if value and len(value) > 1000:
            raise serializers.ValidationError("El mensaje no puede exceder los 1000 caracteres.")
        return value

    def validate_imagen(self, value):
        if value:
            #Validar tamaño máximo de 5MB
            max_size = 5 * 1024 * 1024 # 5 Mb
            if value.size > max_size:
                raise serializers.ValidationError("La imagen excede el límite permitido de 5MB.")
            
            
            if not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                raise serializers.ValidationError("Solo se permiten imágenes en formato PNG o JPG.")
        return value

    def validate(self, data):
        if not data.get('texto') and not data.get('imagen'):
            raise serializers.ValidationError("El mensaje debe contener texto o una imagen.")
        return data