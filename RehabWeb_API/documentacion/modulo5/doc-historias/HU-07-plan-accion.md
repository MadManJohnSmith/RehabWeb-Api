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

- [ ] Prefijo **`/api/v1/`** centralizado en `urls.py`.
- [ ] **`django-cors-headers`:** `CORS_ALLOWED_ORIGINS` con `http://localhost:4200` y prod cuando exista; `CORS_ALLOW_CREDENTIALS` coherente con cookies si se usan.
- [ ] **`REST_FRAMEWORK`:** `TokenAuthentication`, `SessionAuthentication` si admin; `DEFAULT_PERMISSION_CLASSES`; `DEFAULT_FILTER_BACKENDS` con `DjangoFilterBackend`; **`DEFAULT_PAGINATION_CLASS`** y `PAGE_SIZE` documentados.
- [ ] **MySQL:** `utf8mb4`, `CONN_MAX_AGE` razonable; charset en `DATABASES`.
- [ ] **`GET /api/v1/health/`:** `SELECT 1` + JSON `{ "status": "ok" }` (o equivalente).
- [ ] **Logging:** formato útil; en `DEBUG=False` respuestas 500 genéricas al cliente.
- [ ] **`DATA_UPLOAD_MAX_MEMORY_SIZE` / `FILE_UPLOAD_MAX_MEMORY_SIZE`** revisados si HU-02 sube archivos o genera descargas grandes en memoria.
- [ ] **Documentación:** README sección “Cómo obtener token y llamar desde Angular”; alinear con `environment.ts`.

### 3.3 Autenticación transversal

- [ ] Decisión final **Token DRF** vs **JWT** documentada en `Contrato-API-endpoints-DTO-serializers.md`.
- [ ] Si Token: ejemplo Angular `HttpInterceptor` con `Authorization: Token …`.
- [ ] Endpoint de login (`obtain_auth_token` o custom) y flujo de creación de usuario terapeuta en semillas.

---

## 4. Fases de trabajo (orden recomendado)

### Fase 0 — Checklist de arranque del proyecto

- [ ] Variables de entorno (`.env`) para `SECRET_KEY`, DB, `DEBUG` — no secretos en git.
- [ ] Verificar versión Python compatible con Django del `requirements.txt`.

### Fase 1 — Settings y CORS

- [ ] Ajustes en `settings.py` según §3.2.
- [ ] Probar preflight desde navegador (Angular) a API local.

### Fase 2 — Infra DRF global

- [ ] Manejo de excepciones/custom renderer solo si hace falta unificar aún más el JSON de error.
- [ ] Throttling básico (opcional) en endpoints pesados (export, compare).

### Fase 3 — Salud y observabilidad

- [ ] `health` endpoint; opcional middleware `request_id` para correlación logs–front.

### Fase 4 — Coordinación con otras HUs

- [ ] Revisión cruzada: cada integrante usa misma paginación y mismos nombres de query params acordados.
- [ ] Tabla de códigos HTTP → mensaje UI (documento corto en README).

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

*Última revisión del plan: 2026-04-23.*
