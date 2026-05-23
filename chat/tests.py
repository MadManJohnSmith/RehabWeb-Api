from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Mensaje

#python manage.py test chat
#python manage.py test chat -v 2

User = get_user_model()

class MensajeAPITests(APITestCase):
    def setUp(self):
        
        self.paciente = User.objects.create_user(username='paciente1', password='password123')
        self.terapeuta = User.objects.create_user(username='terapeuta1', password='password123')
        
        # endpoint para mensajes
        self.url = '/api/chat/mensajes/'
        #print(f"\n--> setUp ejecutado, usuarios actuales en DB: {User.objects.count()}\n")

    def test_acceso_denegado_sin_autenticacion(self):
        print("\n" + "-"*50)
        print("ACCESO DENEGADO SIN AUTENTICACION")
        print("-"*50 + "\n")
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        print(">>> RESULTADO: Correcto - Código de estado:", response.status_code)
        
    def test_enviar_mensaje_texto_exitoso(self):
        print("\n" + "-"*50)
        print("ENVIAR MENSAJE DE TEXTO EXITOSO")
        print("-"*50 + "\n")
        self.client.force_authenticate(user=self.paciente)
        
        data = {
            'destinatario': self.terapeuta.id,
            'texto': 'Hola doctor, este es un mensaje automatizado de prueba.'
        }
        
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verificamos que se guardó en MySQL
        self.assertEqual(Mensaje.objects.count(), 1)
        self.assertEqual(Mensaje.objects.get().texto, data['texto'])

        print(">>> RESULTADO: Correcto - Código de estado:", response.status_code)

    def test_rechazar_mensaje_largo(self):
        print("\n" + "-"*50)
        print("MENSAJE DEMASIADO LARGO")
        print("-"*50 + "\n")

        self.client.force_authenticate(user=self.paciente)
        
        texto_largo = "A" * 1001 
        data = {
            'destinatario': self.terapeuta.id,
            'texto': texto_largo
        }
        
        response = self.client.post(self.url, data)
        
        # Verificamos que arroje error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Verificamos que no se haya guardado nada en la base de datos
        self.assertEqual(Mensaje.objects.count(), 0)

        print(">>> RESULTADO: Correcto - Código de estado:", response.status_code)

    def test_paginacion_20_mensajes(self):
        print("\n" + "-"*50)
        print("PAGINACION DE MENSAJES")
        print("-"*50 + "\n")
        self.client.force_authenticate(user=self.paciente)
        
        # Crear 25 mensajes
        mensajes = [
            Mensaje(remitente=self.paciente, destinatario=self.terapeuta, texto=f"Mensaje {i}")
            for i in range(25)
        ]
        Mensaje.objects.bulk_create(mensajes)
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verificamos que en los resultados solo vengan 20
        self.assertEqual(len(response.data['results']), 20)
        # Verificamos que la api sea consciente de que hay 25 en total
        self.assertEqual(response.data['count'], 25)

        print(">>> RESULTADO: Correcto - Código de estado:", response.status_code)

    def test_rechazar_imagen_mayor_a_5mb(self):
        print("\n" + "-"*50)
        print("IMAGEN DEMASIADO GRANDE")
        print("-"*50 + "\n")
        self.client.force_authenticate(user=self.paciente)
        
        # Crear un archivo simulado de 6MB
        archivo_pesado = SimpleUploadedFile(
            "foto_pesada.jpg",
            b"0" * (6 * 1024 * 1024),
            content_type="image/jpeg"
        )
        
        data = {
            'destinatario': self.terapeuta.id,
            'imagen': archivo_pesado
        }
        
      
        response = self.client.post(self.url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Mensaje.objects.count(), 0)

        print(">>> RESULTADO: Correcto - Código de estado:", response.status_code)

    def test_rechazar_formato_invalido(self):
        print("\n" + "-"*50)
        print("FORMATO DE ARCHIVO INVALIDO")
        print("-"*50 + "\n")

        self.client.force_authenticate(user=self.paciente)
        
        archivo_pdf = SimpleUploadedFile(
            "reporte.pdf",
            b"contenido falso de pdf",
            content_type="application/pdf"
        )
        
        data = {
            'destinatario': self.terapeuta.id,
            'imagen': archivo_pdf
        }
        
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        print(">>> RESULTADO: Correcto - Código de estado:", response.status_code)

    def test_aislamiento_de_mensajes(self):
        print("\n" + "-"*50)
        print("AISLAMIENTO DE MENSAJES")
        print("-"*50 + "\n")
    
        Mensaje.objects.create(remitente=self.paciente, destinatario=self.terapeuta, texto="Mi diagnóstico secreto")
        
        intruso = User.objects.create_user(username='paciente_intruso', password='password123')
        
        # Autenticamos al intruso y pedimos la lista de mensajes
        self.client.force_authenticate(user=intruso)
        response = self.client.get(self.url)
        
        # Verificamos que el intruso no reciba nada
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

        print(">>> RESULTADO: Correcto - Código de estado:", response.status_code)
