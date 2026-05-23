"""
URL configuration for RehabWeb_API project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/chat/', include('chat.urls')),  # Chat app
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#FUNCIONAR EN ENTORNO DE DESARROLLO, NO EN PRODUCCIÓN
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
