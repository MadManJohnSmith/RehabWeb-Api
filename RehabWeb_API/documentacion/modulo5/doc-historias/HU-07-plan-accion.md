# Plan de acción — HU-07: Infraestructura de interfaz, navegación y contrato estable API

**Propietario sugerido:** Integrante 7 (backend infra) + **equipo front** (AC de UI ya mayormente entregados)  
**Referencias:** Historias HU-07 · Plan backend §Integrante 7 · Reporte front HU-07 · Contrato API (convenciones globales + `health`)

---

## 1. Objetivo de negocio

Experiencia **coherente y responsiva**: navegación por módulos, componentes adaptables, y **manejo explícito** de carga, vacío y error **sin** depender de excepciones silenciosas en consola. En el plan de equipo, esta HU incluye además la **base técnica** del backend para que Angular integre sin ambigüedad.

---

## 2. Criterios de aceptación (historias) → estado y trabajo restante

| AC | Historias | Front (reporte) | Acciones / backend |
|----|-----------|-----------------|-------------------|
| AC-01 | Sidebar colapsable; accesos dashboard, pacientes, reportes, configuración, cierre sesión | `shell-layout`, `shell-sidebar`, drawer móvil | Verificar rutas y labels con producto; **logout** debe invalidar token o sesión según diseño (implementar endpoint si aplica); documentar |
| AC-02 | Mobile friendly: tablas, gráficas, menús | `overflow-x-auto`, `viewBox`, `min-w-0` | Backend no sustituye AC-02; pruebas responsive en dispositivos reales en sprint de QA |
| AC-03 | Estados carga/error; sin consola rota en ausencia de datos | Patrón en `session-history-page`; placeholders “en construcción” | **Contrato API estable:** códigos HTTP claros, cuerpos DRF; **no** tracebacks en prod (`DEBUG=False`); paginación uniforme; opcional `GET /api/v1/health/`; extender patrón de estados a **otras** pantallas cuando dejen de usar mocks |

---

## 3. Alcance dividido (front vs back)

### 3.1 Frontend (cierre HU-07 de producto)

- [ ] Inventario de pantallas que aún usan mocks: añadir **loading / error / empty** al integrar API (dashboard, reportes, alertas, comparativa, pacientes).
- [ ] Revisar rutas placeholder: sustituir por páginas reales a medida que el backend entregue datos.
- [ ] Accesibilidad básica en estados de error (anuncio, botón reintento con `aria-label`).

### 3.2 Backend (plan equipo — prioridad alta temprano)

- [x] Prefijo **`/api/v1/`** centralizado en `urls.py`.
- [x] **`django-cors-headers`:** `CORS_ALLOWED_ORIGINS` con `http://localhost:4200` (y `127.0.0.1`); orígenes extra vía `DJANGO_CORS_EXTRA_ORIGINS`; `CORS_ALLOW_CREDENTIALS=True`.
- [x] **`REST_FRAMEWORK`:** `TokenAuthentication`, `SessionAuthentication`; `DEFAULT_PERMISSION_CLASSES`; `DEFAULT_FILTER_BACKENDS` con `DjangoFilterBackend`; **`DEFAULT_PAGINATION_CLASS`** = `APIPageNumberPagination` (ver `pagination.py`).
- [x] **MySQL:** `utf8mb4`; `CONN_MAX_AGE` configurable (`DB_CONN_MAX_AGE`, por defecto 60 s); credenciales sobreescribibles por variables de entorno.
- [x] **`GET /api/v1/health/`:** `SELECT 1` + JSON `{ "status": "ok" }` o **503** si falla la BD.
- [x] **Logging:** formato en consola (INFO); en `DEBUG=False` Django no expone tracebacks al cliente en 500.
- [x] **`DATA_UPLOAD_MAX_MEMORY_SIZE` / `FILE_UPLOAD_MAX_MEMORY_SIZE`** elevados (26 MiB) para export HU-02.
- [x] **Documentación:** README + **§9** de este plan + `.env.example`.

### 3.3 Autenticación transversal

- [x] Decisión **Token DRF** (no JWT) documentada en `Contrato-API-endpoints-DTO-serializers.md`.
- [x] **Login / logout:** `POST /api/v1/auth/login/` (`obtain_auth_token`), `POST /api/v1/auth/logout/` (borra token). Patrón interceptor en **§9**.
- [ ] Flujo de creación de usuario terapeuta en semillas (comando `seed` / fixtures): responsabilidad del equipo al cerrar datos demo.

---

## 4. Fases de trabajo (orden recomendado)

### Fase 0 — Checklist de arranque del proyecto

- [x] Variables de entorno (`.env` / `.env.example`) para `SECRET_KEY`, DB, `DEBUG` — no secretos en git.
- [x] Verificar versión Python compatible con Django del `requirements.txt`.

### Fase 1 — Settings y CORS

- [x] Ajustes en `settings.py` según §3.2.
- [ ] Probar preflight desde navegador (Angular) a API local (validación manual del equipo).

### Fase 2 — Infra DRF global

- [x] Paginación global alineada con listados HU-05 / HU-06.
- [ ] Throttling básico (opcional) en endpoints pesados (export, compare).

### Fase 3 — Salud y observabilidad

- [x] `health` endpoint; middleware `request_id` opcional / futuro.

### Fase 4 — Coordinación con otras HUs

- [x] Paginación y query `page` / `page_size` documentadas (**§9**, contrato API).
- [x] Tabla de códigos HTTP → mensaje UI en **§9** y README (HU-07).

### Fase 5 — QA conjunto

- [ ] Matriz: cada ruta principal con 401, 403, 200 vacío, 200 con datos.
- [ ] Lighthouse o checklist manual responsive (AC-02).

---

## 5. Definition of Done

- Un desarrollador nuevo puede levantar API + front siguiendo README y ver datos semilla.
- Navegación principal accesible en desktop y móvil según historias.
- Pantallas integradas con API muestran estados de carga/error/vacío sin errores no controlados en consola en flujos normales.

---

## 6. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| CORS roto en prod | Lista explícita de orígenes; no `*` con credenciales |
| Paginación distinta por vista | Regla: salvo excepción documentada, todas usan el mismo schema |
| Front muestra Bearer y API espera Token | Actualizar Baseline-Tokens / UI y contrato en un solo PR |

---

## 7. Dependencias

- **Ninguna otra HU** bloquea los settings base, pero **esta HU debe avanzar antes** del trabajo masivo de integración del resto.

---

## 8. Implementación backend entregada (resumen)

### 8.1 Rutas nuevas

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/health/` | `SELECT 1`; **AllowAny**; `503` si BD caída. |
| POST | `/api/v1/auth/login/` | `obtain_auth_token`; `username`, `password`. |
| POST | `/api/v1/auth/logout/` | Borra token del usuario autenticado → **204**. |

### 8.2 Archivos y settings

| Archivo / área | Rol |
|----------------|-----|
| `RehabWeb_API/pagination.py` | `APIPageNumberPagination` (global + vistas lista). |
| `RehabWeb_API/views/health.py` | `HealthAPIView`. |
| `RehabWeb_API/views/auth_api.py` | `LogoutAPIView`. |
| `RehabWeb_API/api_urls.py` | Rutas `health`, `auth/login`, `auth/logout`. |
| `RehabWeb_API/settings.py` | `python-dotenv`, env DB/CORS/secret, `CONN_MAX_AGE`, límites upload, `DEFAULT_PAGINATION_CLASS`. |
| `requirements.txt` | `python-dotenv`. |
| `.env.example` | Plantilla de variables. |
| `RehabWeb_API/tests/test_infra_hu07.py` | Health, login, logout. |
| `README.md` | Token, health, login, tabla HTTP. |
| `Contrato-API-…md` | Decisión Token DRF y rutas auth. |

### 8.3 Pendiente del equipo

1. Semillas / comando que cree `User` + `Therapist` + token de demo.
2. QA: CORS con despliegue real; matriz 401/403/200 vacío por ruta (Fase 5 del plan).
3. Front: interceptor `Authorization: Token …` y pantallas sin mocks (§3.1).

---

## 9. Apéndice técnico — infraestructura API y Angular

### Autenticación (Token DRF)

| Ruta | Método | Auth | Respuesta |
|------|--------|------|-----------|
| `/api/v1/auth/login/` | POST | No | `200` + `{"token": "<uuid>"}`; cuerpo JSON o form: `username`, `password`. |
| `/api/v1/auth/logout/` | POST | Sí (`Token …`) | `204`; elimina el token del usuario. |

Cabecera habitual: `Authorization: Token <token>`. En Angular: `environment.apiUrl` hacia `.../api/v1/` y `HttpInterceptor` con esa cabecera (no `Bearer` salvo migración JWT acordada).

### Salud

`GET /api/v1/health/` sin auth: `200` + `{"status":"ok"}` tras `SELECT 1`; `503` si la BD no responde.

### CORS

Por defecto `http://localhost:4200`, `http://127.0.0.1:4200`; más orígenes vía `DJANGO_CORS_EXTRA_ORIGINS` (coma-separados). `CORS_ALLOW_CREDENTIALS = True`.

### Paginación

`RehabWeb_API.pagination.APIPageNumberPagination`: defecto 10 filas, máx. 50 vía `page_size`. Listados: `sessions`, `patients`, … Objetos únicos (`dashboard`, `inactivity-alerts`) sin envoltorio `results`.

### Variables de entorno

Plantilla: `.env.example` en la raíz del repo; `settings.py` carga `.env` con `python-dotenv`.

### Códigos HTTP frecuentes (UI)

| Código | Uso típico |
|--------|------------|
| 200 | Éxito con JSON. |
| 204 | Logout. |
| 400 | Validación / credenciales incorrectas (login). |
| 401 | Sin token o inválido. |
| 403 | Sin permiso (p. ej. no terapeuta). |
| 404 | Recurso no accesible. |
| 409 | Conflicto de negocio. |
| 500 | Error interno; con `DEBUG=False` mensaje genérico al cliente. |
| 503 | Health: BD caída. |

---

*Última revisión del plan: 2026-04-23 (secciones 8–9).*
