# RehabWeb-Api

Backend API para la webapp de fisioterapia **RehabWeb**, construido con Django REST Framework y MySQL.

---

## 📋 Tabla de Tecnologías

| Tecnología | Versión |
|---|---|
| Python | 3.12+ |
| Django | 6.0.2 |
| Django REST Framework | 3.16.1 |
| django-cors-headers | 4.9.0 |
| django-filter | 25.2 |
| python-dotenv | 1.0.1 |
| mysqlclient | 2.2.8 |
| openpyxl | 3.1.5 |
| reportlab | 4.4.3 |
| MySQL (XAMPP) | 8.0+ |

---

## 🚀 Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd RehabWeb-Api
```

### 2. Crear y activar entorno virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3b. Variables de entorno (recomendado)

Copia `.env.example` a `.env` en la raíz del repo y ajusta valores (no subas `.env` a git).  
Django carga `.env` automáticamente vía `python-dotenv` en `settings.py`. Así puedes fijar `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, credenciales `MYSQL_*`, orígenes CORS extra (`DJANGO_CORS_EXTRA_ORIGINS`), etc.

### 4. Configurar base de datos

1. Asegúrate de que **MySQL** esté corriendo (por ejemplo, via XAMPP).
2. Crea la base de datos `rehab_db`:

```sql
CREATE DATABASE rehab_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. Verifica la conexión: por defecto coincide con XAMPP local; también puedes definir `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST` y `MYSQL_PORT` en `.env`.

### 5. Ejecutar migraciones

```bash
python manage.py migrate
```

### 6. Crear superusuario (opcional)

```bash
python manage.py createsuperuser
```

### 7. Iniciar servidor de desarrollo

```bash
python manage.py runserver
```

El servidor estará disponible en: `http://127.0.0.1:8000/`

---

## 🔌 API Módulo 5 — Infraestructura (HU-07)

Comprobar que la API y la base de datos responden (sin token):

```bash
curl -s http://127.0.0.1:8000/api/v1/health/
```

Obtener token DRF (usuario y contraseña Django existentes):

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"username\": \"tu_usuario\", \"password\": \"tu_contraseña\"}"
```

Invalidar el token actual (cerrar sesión en cliente):

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/logout/ ^
  -H "Authorization: Token <TOKEN>"
```

En Angular, usa la misma URL base que en `environment.ts` (p. ej. `http://127.0.0.1:8000/api/v1/`) y un interceptor que envíe `Authorization: Token <clave>` (no `Bearer`, salvo migración a JWT acordada).

| HTTP | Significado típico |
|------|---------------------|
| 200 | Éxito con JSON. |
| 204 | Logout correcto. |
| 400 | Validación / credenciales incorrectas en login. |
| 401 | Sin token o token inválido. |
| 403 | Sin permiso (p. ej. no terapeuta). |
| 404 | Recurso no encontrado o no autorizado para ese terapeuta. |
| 503 | Health: base de datos no disponible. |

- Listados paginados (`sessions`, `patients`, …): parámetros `page` y `page_size` (máx. 50); respuesta con `count`, `next`, `previous`, `results`.
- Documentación ampliada: `RehabWeb_API/documentacion/modulo5/doc-historias/HU-07-plan-accion.md` (§9)

---

## 🔌 API Módulo 5 — Dashboard (HU-01)

Tras aplicar migraciones del proyecto (`makemigrations` / `migrate`) y crear un **terapeuta** (`Therapist` ligado al `User`) con datos de prueba (`Patient`, `TherapistPatient`, `Session`, `MetricPoint`), podrás probar:

Obtener métricas del usuario autenticado (token DRF):

```bash
curl -s -H "Authorization: Token <TOKEN_DE_SALIDA_DEL_SEED>" http://127.0.0.1:8000/api/v1/me/dashboard/
```

- Ruta: `GET /api/v1/me/dashboard/`
- Cabecera: `Authorization: Token <clave>` (no `Bearer`, salvo que el proyecto migre a JWT).
- Esquema JSON: `RehabWeb_API/documentacion/modulo5/doc-historias/HU-01-plan-accion.md` (§9)

**Tests sin MySQL:** `python manage.py test` usa SQLite en memoria (ver `settings.py`).

---

## 🔌 API Módulo 5 — Exportación clínica (HU-02)

Tras migrar y tener **terapeuta**, vínculo activo con el paciente y sesiones en el rango de fechas:

```bash
curl -s -X POST "http://127.0.0.1:8000/api/v1/reports/export/" ^
  -H "Authorization: Token <TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d "{\"patientId\": 1, \"dateFrom\": \"2026-01-01\", \"dateTo\": \"2026-01-31\", \"format\": \"pdf\"}" ^
  --output informe.pdf
```

En bash (macOS/Linux) omitir `^` y usar comillas simples en el JSON si prefieres.

- Ruta: `POST /api/v1/reports/export/`
- Cuerpo JSON (camelCase): `patientId`, `dateFrom`, `dateTo`, `format` (`pdf` o `xlsx`).
- Documentación: `RehabWeb_API/documentacion/modulo5/doc-historias/HU-02-plan-accion.md` (§9)

---

## 🔌 API Módulo 5 — Alertas de inactividad (HU-03)

Listado en vivo (misma regla que el resumen del dashboard: más de 3 días sin sesión):

```bash
curl -s -H "Authorization: Token <TOKEN>" http://127.0.0.1:8000/api/v1/inactivity-alerts/
```

Job diario que materializa la tabla `InactivityAlert` (tras migrar):

```bash
python manage.py refresh_inactivity_alerts
```

Ejemplo **cron** (Linux, 06:00): `0 6 * * * cd /ruta/RehabWeb-Api && .venv/bin/python manage.py refresh_inactivity_alerts`

- Ruta: `GET /api/v1/inactivity-alerts/` · query opcional: `?patientId=1`
- Documentación: `RehabWeb_API/documentacion/modulo5/doc-historias/HU-03-plan-accion.md` (§9)

---

## 🔌 API Módulo 5 — Comparativa de desempeño (HU-04)

Serie temporal (meta vs observado) para un paciente vinculado:

```bash
curl -s -H "Authorization: Token <TOKEN>" http://127.0.0.1:8000/api/v1/patients/1/performance-series/
```

Comparativa multi-paciente (cuerpo JSON):

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/performance/compare/ ^
  -H "Authorization: Token <TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d "{\"patientIds\": [1, 2]}"
```

- Rutas: `GET …/patients/<id>/performance-series/` · `POST …/performance/compare/`
- Documentación: `RehabWeb_API/documentacion/modulo5/doc-historias/HU-04-plan-accion.md` (§9)

---

## 🔌 API Módulo 5 — Historial de sesiones (HU-05)

Lista paginada (ejemplo `page_size=10`):

```bash
curl -s -H "Authorization: Token <TOKEN>" "http://127.0.0.1:8000/api/v1/sessions/?page=1&page_size=10"
```

Detalle de una sesión:

```bash
curl -s -H "Authorization: Token <TOKEN>" http://127.0.0.1:8000/api/v1/sessions/1/
```

- Filtros opcionales: `patientId`, `search`, `ordering`.
- Documentación: `RehabWeb_API/documentacion/modulo5/doc-historias/HU-05-plan-accion.md` (§9)

---

## 🔌 API Módulo 5 — Pacientes y vínculos (HU-06)

Lista de pacientes del terapeuta (paginada):

```bash
curl -s -H "Authorization: Token <TOKEN>" "http://127.0.0.1:8000/api/v1/patients/?page=1&page_size=10"
```

Vincular paciente (cuerpo JSON):

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/patients/link/ ^
  -H "Authorization: Token <TOKEN>" ^
  -H "Content-Type: application/json" ^
  -d "{\"associationId\": \"ID-001\", \"fullName\": \"Nombre Apellido\", \"clinicalStatus\": \"activo\"}"
```

Ficha por id de paciente:

```bash
curl -s -H "Authorization: Token <TOKEN>" http://127.0.0.1:8000/api/v1/patients/1/
```

- Filtros opcionales en lista: `q`, `clinicalStatus`, `includeDeleted`.
- Mutaciones sobre el vínculo: `PATCH /api/v1/therapist-patients/<linkId>/`, `POST .../unlink/`, `POST .../restore/`.
- Documentación: `RehabWeb_API/documentacion/modulo5/doc-historias/HU-06-plan-accion.md` (§9)

---

## 📁 Estructura del proyecto

```
RehabWeb-Api/
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
└── RehabWeb_API/
    ├── __init__.py
    ├── settings.py
    ├── urls.py
    ├── api_urls.py
    ├── wsgi.py
    ├── asgi.py
    ├── admin.py
    ├── models.py
    ├── serializers.py
    ├── filters.py
    ├── pagination.py
    ├── permissions.py
    ├── services/
    ├── management/commands/
    │   └── refresh_inactivity_alerts.py   # (+ otros comandos que añada el equipo)
    ├── views/
    │   ├── __init__.py
    │   ├── auth_api.py
    │   ├── dashboard.py
    │   ├── health.py
    │   ├── inactivity.py
    │   ├── patient_management.py
    │   ├── performance.py
    │   ├── reports.py
    │   └── sessions.py
    ├── tests/
    ├── documentacion/modulo5/…
    └── migrations/
        └── __init__.py         # migraciones iniciales: generarlas con makemigrations
```

---

## 🌿 Estrategia de Branching

Este proyecto sigue una estrategia de branching por equipos con revisión en staging.

### Diagrama de flujo

```
main ← staging ← equipo/{nombre} ← dev/{nombre-desarrollador}
```

### Ramas principales

| Rama | Propósito | ¿Quién hace merge aquí? |
|------|-----------|-------------------------|
| `main` | Producción estable. Solo código probado y aprobado. | Líder del proyecto tras aprobación en staging |
| `staging` | Rama de integración y pruebas. Aquí se valida que todos los equipos funcionen juntos. | Líderes de equipo |
| `equipo/equipo-1` | Rama principal del Equipo 1. | Los desarrolladores del Equipo 1 |
| `equipo/equipo-2` | Rama principal del Equipo 2. | Los desarrolladores del Equipo 2 |
| `equipo/equipo-3` | Rama principal del Equipo 3. | Los desarrolladores del Equipo 3 |
| `equipo/equipo-4` | Rama principal del Equipo 4. | Los desarrolladores del Equipo 4 |
| `equipo/equipo-5` | Rama principal del Equipo 5. | Los desarrolladores del Equipo 5 |
| `equipo/equipo-6` | Rama principal del Equipo 6. | Los desarrolladores del Equipo 6 |
| `dev/{nombre}` | Rama personal de cada desarrollador (ej: `dev/juan-lopez`). | El desarrollador individual |

### Flujo de trabajo

1. **Cada desarrollador** trabaja en su rama personal `dev/{nombre}`.
2. Al terminar su sprint o tarea asignada, el desarrollador crea un **Pull Request** hacia la rama de su equipo `equipo/{nombre}`.
3. El **líder de equipo** revisa el PR y hace merge a `equipo/{nombre}`.
4. Cuando el equipo completa su sprint, el líder crea un **Pull Request** de `equipo/{nombre}` → `staging`.
5. En `staging` se ejecutan **pruebas de integración** para verificar que todo funcione en conjunto.
6. Si las pruebas pasan, se crea un **Pull Request** de `staging` → `main`.

### Convención de commits

Usar el formato **Conventional Commits**:

```
<tipo>(<alcance>): <descripción corta>

[cuerpo opcional]
```

#### Tipos permitidos

| Tipo | Uso |
|------|-----|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Cambios en documentación |
| `style` | Formato, punto y coma faltantes, etc. (no cambia lógica) |
| `refactor` | Refactorización de código (no agrega ni corrige) |
| `test` | Agregar o corregir tests |
| `chore` | Tareas de mantenimiento (dependencias, configs) |

#### Ejemplos

```
feat(auth): agregar endpoint de login con JWT
fix(formulario): corregir validación de email en registro
docs(readme): actualizar instrucciones de instalación
refactor(servicios): extraer lógica de HTTP a servicio base
chore(deps): actualizar Angular a v20.3
```

### Reglas importantes

> ⚠️ **NUNCA** hacer push directo a `main` o `staging`.
>
> ⚠️ **SIEMPRE** crear Pull Requests para cualquier merge entre ramas.
>
> ⚠️ Antes de crear un PR, hacer `git pull` de la rama destino para evitar conflictos.
