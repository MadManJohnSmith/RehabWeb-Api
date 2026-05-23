from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MensajeViewSet

# Usamos un router de DRF para generar las rutas automáticamente
router = DefaultRouter()
router.register(r'mensajes', MensajeViewSet, basename='mensaje')

urlpatterns = [
    path('', include(router.urls)),
]