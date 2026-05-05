# Plan de trabajo backend — Módulo 5 (PhysioMetrics / RehabWeb)

Este documento traduce lo que ya existe en **frontend + mocks** a **qué hay que construir en backend y base de datos** para que la app funcione de punta a punta. Está pensado para un **equipo de 7 integrantes** alineado con las **7 historias de usuario** del módulo (`Historias de Usuario Modulo 5.md`).

> **Nota:** La asignación “Integrante 1 … 7” es una **propuesta de reparto por HU**. En la práctica pueden rotar tareas, pero cada bloque lista el **alcance backend** mínimo que esa HU exige.

---

## 0. Núcleo tecnológico del backend (cómo está armado el proyecto)

Así está pensado vuestro stack; todo lo demás en este documento **encaja en estas piezas** (no asumimos otro framework ni otra base de datos salvo que el equipo decida cambiarlo).

| Pieza | Versión / rol | Qué es, en pocas palabras |
|-------|----------------|---------------------------|
| **Django** | 6.0.2 | Framework web de Python: define **rutas (URLs)**, **modelos** (tablas en código), **panel de administración**, **middleware** (código que se ejecuta antes/después de cada petición), plantillas si las usáis, etc. (es el “esqueleto” del servidor). |
| **Django REST Framework (DRF)** | 3.16.1 | Capa encima de Django para **API REST**: convierte modelos en **JSON** mediante **serializers** (reglas de entrada/salida), **vistas** (qué pasa en cada URL), **permisos** (quién puede ver o editar qué). |
| **Autenticación** | `rest_framework.authtoken` + **sesión** | **Token:** el front (Angular) guarda una clave y la envía en cada petición; el servidor sabe quién es sin cookies de sesión del navegador. **Sesión:** útil sobre todo para **login en el admin de Django** o flujos basados en cookie. (el token es como un “pase” fijo hasta que se revoca). |
| **django-cors-headers** | (según `requirements.txt`) | Permite que el **navegador** llame a la API desde otro origen (p. ej. Angular en `http://localhost:4200`) sin bloquearse; se configura en `settings.py` apuntando al cliente Angular. (CORS = reglas del navegador para llamadas entre sitios distintos). |
| **django-filter** | (según `requirements.txt`) | En listados de la API, añade **filtros por query string** (`?nombre=`, `?estado=`) usando `DjangoFilterBackend` en DRF. (evita escribir a mano cada filtro en cada vista). |
| **mysqlclient** | (según `requirements.txt`) | Conector Python ↔ **MySQL**; Django lo usa como motor de base de datos. |
| **Base de datos** | MySQL, `ENGINE = django.db.backends.mysql`, host típico `127.0.0.1:3306`, base **`rehab_db`** (p. ej. vía XAMPP) | Donde viven tablas, índices y datos reales. (XAMPP = entorno local que levanta MySQL en tu máquina). |
| **Despliegue del proceso web** | **WSGI** (`wsgi.py`) y **ASGI** (`asgi.py`) | Punto de entrada para el **servidor HTTP** (Gunicorn, uWSGI, Daphne, etc.): WSGI es el estándar clásico; ASGI sirve si más adelante usáis WebSockets o apps async. (archivos que “arranca” el hosting). |
| **Logging** | Logging estándar de Python → **consola** | Mensajes de error, avisos y depuración visibles en la terminal o en los logs del servidor. (para saber qué falló cuando algo rompe). |
| **Dependencias de soporte** | `asgiref`, `sqlparse`, `tzdata` | Librerías que Django y el ecosistema async suelen traer: **zonas horarias**, parsing SQL, utilidades ASGI. (normalmente no las tocáis directamente). |

**Resumen en una frase:** API REST con **Django + DRF**, datos en **MySQL** (`rehab_db`), **CORS** abierto hacia Angular en `localhost:4200`, listados filtrables con **django-filter**, y login del terapeuta vía **token** (y sesión donde aplique).

---

## 1. Qué tenemos que construir en el backend (visión general, ya “en clave Django”)

Para sustituir mocks y `localStorage` por un sistema real, el equipo debe entregar al menos:

| Capa | Qué implica (técnico) | Para quien no domina el argot |
|------|----------------------|-------------------------------|
| **API REST versionada** | URLs en `urls.py`, vistas DRF (`APIView`, `ViewSet`, `ReadOnlyModelViewSet`, etc.), prefijo tipo `/api/v1/...`. | Rutas claras que el Angular pueda llamar con `HttpClient` y que no cambien sin aviso. |
| **Modelos + migraciones** | `models.Model` en apps Django, `makemigrations` / `migrate`. | Las tablas de MySQL se crean y versionan desde código (no “a mano” sin registro). |
| **Autenticación y permisos DRF** | `TokenAuthentication` en `DEFAULT_AUTHENTICATION_CLASSES`, `IsAuthenticated`, permisos custom tipo “solo ve pacientes vinculados a este usuario terapeuta”. | Sin token válido no hay datos; con token, solo lo que le toca a ese terapeuta. |
| **Reglas de negocio** | En **serializers** (`validate_*`), en **servicios** (funciones/clases aparte) o en **signals** si son puntuales; cálculo de inactividad **> 3 días**, soft delete, etc. | La lógica “de negocio” no solo en el front: el servidor es quien manda en datos sensibles. |
| **Tareas programadas** | **Management command** de Django (`python manage.py generar_alertas_inactividad`) + **Tarea programada del sistema** (cron en Linux, Programador de tareas en Windows, o servicio en la nube) que lo ejecute **cada día**. (Opcional más adelante: Celery + broker; no es obligatorio si el cron cubre el AC). | Un proceso que “se despierta solo” una vez al día para marcar inactivos. |
| **Generación PDF / Excel** | Vista o tarea que lea modelos, renderice plantilla (HTML→PDF con WeasyPrint/wkhtmltopdf, o reportlab) y Excel (openpyxl, xlsxwriter). | El servidor arma el archivo y lo devuelve o deja un enlace de descarga. |
| **Filtros y paginación** | `django-filter` + `PageNumberPagination` (o cursor) en DRF. | Listas largas en páginas y búsquedas por parámetros en la URL. |
| **Rendimiento y calidad** | `select_related` / `prefetch_related`, índices en MySQL, `only()` / `defer()` donde haga falta; respuestas de error uniformes (`ValidationError` → 400). | Menos consultas repetidas, respuestas más rápidas y mensajes entendibles para la UI. |

**Entregables transversales recomendados**

- **Documentación de API**: schema OpenAPI con **drf-spectacular** o similar *(si el equipo la añade)*; si no, al menos README con tablas de endpoints. (lista de URLs y ejemplos de JSON).
- **Convención de errores**: aprovechar el formato de DRF (`{"detail": "..."}` o campos por campo) y documentar qué muestra Angular en cada código. (el front sabe qué mensaje mostrar).
- **Migraciones Django** en el repo (no editar producción sin migración). (historial de cambios de base de datos).
- **Fixtures o comando `loaddata` / factory** para datos de demo alineados con el front. (datos de prueba repetibles).

---

## 2. Base de datos que necesitamos (MySQL + modelos Django, derivada del frontend)

Motor: **MySQL** (`rehab_db`). En Django cada tabla suele mapear a un **`models.Model`**; los tipos “flexibles” pueden ser **`JSONField`** (MySQL 5.7+) o tablas hijas normalizadas.

### 2.1 Identidad y vínculo terapeuta–paciente

| Modelo / tabla (lógico) | Propósito (según front) | Nota sencilla |
|-------------------------|-------------------------|---------------|
| **`User`** (Django `auth.User` o modelo usuario custom) | Quién inicia sesión; se enlaza al token. | La cuenta con la que el terapeuta entra. |
| **`Therapist`** (perfil 1:1 con `User`) | Datos del profesional si van más allá del usuario. | “Ficha” del terapeuta enlazada al login. |
| **`Patient`** | Persona atendida: nombre, datos mínimos, identificador externo opcional. | El paciente como persona en el sistema. |
| **`TherapistPatient`** (tabla intermedia) | Relación terapeuta ↔ paciente: `diagnosis`, `clinical_status` (`riesgo` / `activo` / `alta`), `deleted_at` (soft delete), clave externa de vinculación. | Lista de “mis pacientes” y formulario de vincular (HU-06). |

**Índices sugeridos en MySQL:** `(therapist_id, deleted_at)`, `(therapist_id, clinical_status)`, índice en búsqueda por nombre de paciente / `external_id` si filtráis mucho.

### 2.2 Sesiones e historial (HU-05 + parte de HU-01 / HU-03)

| Modelo / tabla | Propósito | Nota sencilla |
|----------------|-----------|---------------|
| **`Session`** | `patient`, `therapist`, `occurred_at`, `program_label`, `duration_min`, `score`, `status` (texto o choices). | Cada cita o sesión de rehabilitación. |
| **`SessionNote`** o campos en `Session` | Notas clínicas, adherencia %, etc. | Lo que el terapeuta escribió después de la sesión. |
| **`SessionExercise`** | FK a `Session`, nombre, series/reps, notas. | Detalle del “qué se hizo” en esa sesión. |

**Índices:** `(patient_id, occurred_at DESC)` para listado y para “última sesión” por paciente (inactividad).

### 2.3 Métricas para dashboard y comparativa (HU-01, HU-04)

| Modelo / tabla | Propósito | Nota sencilla |
|----------------|-----------|---------------|
| **`MetricPoint`** (normalizado) | `patient` o cohorte, `metric_type`, `period_label`, `meta_value`, `observed_value`, fechas. | Puntos para gráficas “meta vs real” y ROM por semana. |
| **`DashboardSnapshot` / rollup** (opcional) | Agregados precalculados por terapeuta o cohorte. | Tabla “resumen” para que el dashboard cargue más rápido. |

La comparativa multi-paciente es una **query** sobre `MetricPoint` filtrando por varios IDs que el terapeuta tenga permitidos.

### 2.4 Alertas de inactividad (HU-03)

| Modelo / tabla | Propósito | Nota sencilla |
|----------------|-----------|---------------|
| **`InactivityAlert`** (opcional) | Filas generadas/actualizadas por el comando diario: días sin sesión, severidad, etc. | Lista que lee el front en `/app/alertas` sin recalcular todo en cada click. |

Alternativa: calcular solo al **GET** (más simple al inicio, más carga en cada visita).

### 2.5 Exportación de reportes (HU-02)

| Modelo / tabla | Propósito | Nota sencilla |
|----------------|-----------|---------------|
| **`ExportJob`** (opcional) | Cola: paciente, fechas, formato `pdf`/`xlsx`, estado, ruta de archivo o error. | Si el PDF tarda, el usuario puede “esperar” o recibir enlace cuando termine. |

### 2.6 Auditoría (recomendado)

| Modelo / tabla | Propósito | Nota sencilla |
|----------------|-----------|---------------|
| **`AuditLog`** | Quién hizo qué (exportar, desvincular, cambiar diagnóstico). | Rastro por si hay dudas o reclamos. |

---

## 3. Historia por historia — qué debe hacer cada integrante en el backend (Django + DRF)

La numeración **Integrante 1 … 7** corresponde a **HU-01 … HU-07**. Donde antes decíamos “JWT”, en vuestro proyecto la API usa **Token DRF** (`Authorization: Token <clave>`) salvo que migréis a JWT más adelante.

---

### Integrante 1 — HU-01: Dashboard de progreso visual

**Objetivo backend:** un endpoint DRF que devuelva un **JSON agregado** (equivalente al `DashboardMetricsDto` del front) en **menos de ~3 s** con datos reales desde MySQL.

**Tareas concretas (Django)**

- Modelos o lectura sobre `MetricPoint` / `Session` + **consultas agregadas** (`annotate`, `Subquery`, o SQL raw documentado).
- Vista dedicada: p. ej. `GET /api/v1/me/dashboard/` con `permission_classes = [IsAuthenticated]` y filtro “solo datos de mis pacientes”.
- Serializer de solo lectura (nested) para la forma exacta que espera Angular.
- Optimizar: `select_related`/`prefetch_related`, índices MySQL, límite de semanas en query; opcional **caché** (`django.core.cache`) por terapeuta con TTL corto.
- Test con `APITestCase` y/o `pytest-django` midiendo que la vista responde y la forma del JSON es la acordada.

**Criterios de aceptación backend:** datos salen de **MySQL** vía Django (AC-01), tiempo razonable (AC-03).

*(Serializer = molde del JSON; View = la URL que responde; annotate = cálculos en base de datos.)*

---

### Integrante 2 — HU-02: Generación de reportes clínicos

**Objetivo backend:** un **action** o vista `POST` que reciba `patient_id`, `date_from`, `date_to`, genere **PDF** y **Excel** con los mismos filtros obligatorios, y solo para usuario autenticado con rol de terapeuta.

**Tareas concretas (Django)**

- Dependencias nuevas en `requirements.txt` (ej. generador PDF + Excel) y política de plantillas (HTML + CSS o librería pura Python).
- Vista o `ViewSet` con `@action(detail=False, methods=['post'])` tipo `export_pdf` / `export_xlsx`, o un solo endpoint con parámetro `format`.
- **Permisos:** `IsAuthenticated` + permiso custom “este `patient_id` está en `TherapistPatient` del `request.user`”.
- **Validación** en serializer: rango de fechas, paciente obligatorio, anti-abuso (límite de rango en días).
- Respuesta: `FileResponse` / `HttpResponse` con `content_type` correcto, o creación de `ExportJob` + URL de descarga.
- Opcional: registrar en `AuditLog` cada exportación.

**Criterios de aceptación backend:** archivos reales (AC-01), filtros validados (AC-02), sin token no hay reporte (AC-03) — con **token DRF**, no JWT, salvo que cambiéis el diseño.

*(FileResponse = el navegador recibe un archivo para descargar.)*

---

### Integrante 3 — HU-03: Alertas proactivas de inactividad

**Objetivo backend:** regla **> 3 días** desde la última `Session` por paciente vinculado, ejecutada **al menos una vez al día**; la API expone la lista para el banner y la página de alertas.

**Tareas concretas (Django)**

- **Management command** `python manage.py refresh_inactivity_alerts` que: recorra `TherapistPatient` activos, calcule `days_since_last_session`, cree/actualice `InactivityAlert` o solo deje datos listos en tabla auxiliar.
- Documentar en README cómo programar el comando en **cron** (Linux) o **Programador de tareas** (Windows) contra el `venv` correcto.
- `GET /api/v1/inactivity-alerts/` con filtros django-filter (por severidad, paciente, etc.) si aplica.
- Opcional: `PATCH` para marcar alerta como “vista”.

**Criterios de aceptación backend:** periodicidad real del job + criterio **> 3 días** coherente con negocio.

*(Management command = script oficial de Django invocable por línea de comandos.)*

---

### Integrante 4 — HU-04: Comparativa de desempeño

**Objetivo backend:** series **meta vs observado** por paciente y endpoint que acepte **varios pacientes** (siempre autorizados para el terapeuta).

**Tareas concretas (Django)**

- `GET /api/v1/patients/<pk>/performance-series/` (lectura de `MetricPoint` filtrada).
- `POST /api/v1/performance/compare/` con body `{"patient_ids": [...]}`: validar longitud máxima, que todos pertenezcan al terapeuta, devolver estructura por paciente.
- Lógica de fórmula (`M0`, `M*`, `R`) en función pura Python + tests unitarios.
- Reutilizar queryset base para no duplicar reglas de permiso.

**Criterios de aceptación backend:** cálculo por capas/paciente (AC-01), varios pacientes en una misma operación de API (AC-02).

---

### Integrante 5 — HU-05: Historial técnico de sesiones

**Objetivo backend:** listado **paginado en servidor** (DRF pagination), orden **descendente** por fecha, y **detalle** en `GET` por id de sesión.

**Tareas concretas (Django)**

- `SessionViewSet` o `ListAPIView` + `RetrieveAPIView` con `filterset_class` (django-filter: por `patient_id`, búsqueda `q` en `program_label` o notas si lo definís).
- Serializer list vs serializer detalle (con `SessionExercise` anidados) para evitar payloads enormes en el listado.
- `get_queryset()` restringido a sesiones de pacientes del `request.user` (vía `TherapistPatient`).

**Criterios de aceptación backend:** paginación real (`count`, `next`, `previous` o el esquema que acordéis con front), detalle async por id.

*(get_queryset = “de dónde salen las filas” según el usuario logueado.)*

---

### Integrante 6 — HU-06: Gestión y asociación de pacientes (CRUD)

**Objetivo backend:** persistir en MySQL lo que hoy simula `PatientsRegistryService` / `localStorage`.

**Tareas concretas (Django)**

- `PatientViewSet` o combinación list/create/update con **filtros** (nombre, estado clínico, incluir borrados si `?include_deleted=`).
- Acción custom `link` (`POST .../patients/link/`) que cree `Patient` + `TherapistPatient` con validación de identificador externo.
- `PATCH` sobre vínculo para diagnóstico / `clinical_status`.
- Soft delete: `POST .../unlink/` o `destroy` que setee `deleted_at` en `TherapistPatient`.
- Admin Django opcional para soporte interno (solo staff).

**Criterios de aceptación backend:** vincular, buscar, editar, borrado lógico, estados — todo validado en serializers.

---

### Integrante 7 — HU-07: Infraestructura y contrato estable (Django / DRF / despliegue)

**Objetivo backend:** CORS, settings, logging, paginación global, manejo de errores y salud del servicio para que Angular no “adivine”.

**Tareas concretas (Django)**

- Revisar **`django-cors-headers`**: `CORS_ALLOWED_ORIGINS` incluye `http://localhost:4200` (y el dominio de prod cuando exista). (el navegador permite llamar a la API desde el front).
- **`REST_FRAMEWORK`** en `settings.py`: `DEFAULT_AUTHENTICATION_CLASSES` con `TokenAuthentication` (+ `SessionAuthentication` si lo usáis para admin), `DEFAULT_PERMISSION_CLASSES`, `DEFAULT_FILTER_BACKENDS` con `DjangoFilterBackend`, `DEFAULT_PAGINATION_CLASS`.
- **`DATABASES`**: MySQL `rehab_db`, charset `utf8mb4`, `CONN_MAX_AGE` razonable para no agotar conexiones.
- **Tamaño máximo** de subida (`DATA_UPLOAD_MAX_MEMORY_SIZE`) acorde a exportaciones si subís archivos.
- Vista simple `GET /api/v1/health/` (o `/health/`) que haga `SELECT 1` y devuelva 200 (útil para monitoreo).
- Logging: formato con **request id** si añadís middleware (opcional); nunca devolver **tracebacks** completos al cliente en `DEBUG=False`.

**Criterios de aceptación backend:** respuestas HTTP y cuerpos de error predecibles; documentación de cómo obtener token y llamar desde Angular.

*(settings.py = archivo central de configuración del proyecto Django.)*

---

## 4. Cierre y siguiente paso sugerido para el equipo

1. **Reunión corta (1 h):** repasar modelos Django vs pantallas Angular; fijar nombres de campos en serializers (camelCase vs snake_case: acordar **camelCase en JSON** con `djangorestframework-camel-case` o convención manual).
2. **Lista de endpoints** en README o OpenAPI antes de que Integrante 2 cierre PDFs complejos.
3. **Datos semilla:** comando `manage.py` que cree terapeuta, token, pacientes y sesiones de ejemplo (reproducir mocks del front).

*Documento alineado con: Django 6.0.2, DRF 3.16.1, token + sesión, django-cors-headers, django-filter, MySQL (`rehab_db`), WSGI/ASGI y logging a consola.*
