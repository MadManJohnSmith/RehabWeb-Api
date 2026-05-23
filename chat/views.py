from rest_framework import viewsets, permissions, serializers, status
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db.models import Q
from .models import Mensaje

class MensajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensaje
        fields = ['id', 'remitente', 'destinatario', 'texto', 'imagen', 'estado', 'creado_en']
        read_only_fields = ['id', 'estado', 'creado_en', 'remitente']

    def validate_texto(self, value):
        # máximo 1000 caracteres
        if value and len(value) > 1000:
            raise serializers.ValidationError("El mensaje no puede exceder los 1000 caracteres.")
        return value

    def validate_imagen(self, value):
        if value:
            # validar tamaño máximo de 5MB
            max_size = 5 * 1024 * 1024 # 5 MB
            if value.size > max_size:
                raise serializers.ValidationError("La imagen excede el límite permitido de 5MB.")
            
            # Validar formato permitido
            if not value.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                raise serializers.ValidationError("El archivo debe ser una imagen PNG o JPG.")
        return value

    def validate(self, data):
        # Asegurar que al menos se envíe texto o imagen
        if not data.get('texto') and not data.get('imagen'):
            raise serializers.ValidationError("Debe enviar un texto o una imagen multimedia.")
        return data

# --- paginación ---
class ChatPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50

# --- viwset ---
class MensajeViewSet(viewsets.ModelViewSet):
    
    serializer_class = MensajeSerializer
    pagination_class = ChatPagination
    
    #clases para que potman reconozca las credenciales
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtra los mensajes para que el usuario solo vea sus propias conversaciones.
        """
        user = self.request.user
        contacto_id = self.request.query_params.get('contacto_id')
        
        # obtenemos mensajes donde el usuario sea remitente o destinatario
        qs = Mensaje.objects.filter(
            Q(remitente=user) | Q(destinatario=user)
        )
        
        # Si se especifica un chat específico, filtramos por el contacto
        if contacto_id:
            qs = qs.filter(
                Q(remitente_id=contacto_id) | Q(destinatario_id=contacto_id)
            )
            
        # consulta a la base de datos MySQL (Join)
        return qs.select_related('remitente', 'destinatario')

    def perform_create(self, serializer):
        serializer.save(remitente=self.request.user, estado='Enviado')