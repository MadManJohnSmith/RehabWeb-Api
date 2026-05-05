# Plan de acción — HU-05: Historial técnico de sesiones

**Propietario sugerido:** Integrante 5  
**Referencias:** Historias HU-05 · Plan backend §Integrante 5 · Reporte front HU-05 · Contrato API (`GET /api/v1/sessions/`, `GET /api/v1/sessions/{id}/`)

---

## 1. Objetivo de negocio

Revisar sesiones históricas con **lista paginada** (orden cronológico **descendente**) y **detalle** cargado de forma **asíncrona** al expandir/seleccionar fila, sin recargar toda la página (`/app/historial-sesiones`).

---

## 2. Criterios de aceptación → trazabilidad

| AC | Historias | Front (reporte) | Backend |
|----|-----------|-----------------|---------|
| AC-01 | Lista DESC + paginación servidor/cliente | Tabla DESC; page size 5/10/15; `SessionHistoryApiService.searchSessions` con timer mock | `PageNumberPagination` (o esquema acordado); `ordering=-occurred_at` por defecto; filtros `patientId`, búsqueda texto |
| AC-02 | AJAX al seleccionar sesión | Panel lateral; `getSessionDetail` con delay + JSON estático | `GET` detalle por `id` con `SessionDetailSerializer` (notas, ejercicios, adherencia); respuesta rápida y estable |

---

## 3. Estado actual

- **Frontend:** `session-history-page`, `toSignal` + `combineLatest` + `switchMap`; estados **carga / error / vacío** y reintento (HU-07 alineado). Pendiente: `SessionHistoryApiService` contra rutas reales.
- **Backend:** `SessionViewSet` (lista + detalle), modelo **`SessionExercise`**, filtros y paginación. Migraciones: a cargo del equipo.

---

## 4. Fases de trabajo

### Fase 0 — Contrato de listado vs detalle

- [ ] Listar campos exactos de la **tabla** (liviano) vs **panel** (completo) — evitar payload masivo en lista.
- [ ] Alinear `page_size` del front (5, 10, 15) con `page_size_query_param` en DRF.

### Fase 1 — Modelo Django

- [ ] `Session`: FK `patient`, `therapist`, `occurred_at`, `program_label`, `duration_min`, `score`, `status`, campos de nota/adherencia según UI.
- [ ] `SessionExercise`: FK `session`, nombre, series, repeticiones, notas.
- [ ] Índice compuesto `(patient_id, occurred_at DESC)` para listado e inactividad (HU-03).

### Fase 2 — API lista

- [ ] `SessionViewSet` list con `get_queryset()` restringido a pacientes del terapeuta vía `TherapistPatient`.
- [ ] `django-filter`: `patient_id`, parámetro `search`/`q` sobre etiquetas o notas según AC de producto.
- [ ] Serializer lista: campos mínimos + `patient_display_name` si hace falta para la tabla.

### Fase 3 — API detalle

- [ ] `retrieve` con `prefetch_related('exercises')` o equivalente.
- [ ] 404 para id inexistente o de paciente no autorizado (403 vs 404 — **acordar convención**).

### Fase 4 — Tests

- [ ] Paginación: `count`, `next`, `previous`, `results`.
- [ ] Orden: primera fila la fecha más reciente con datos semilla.
- [ ] Seguridad: usuario A no ve sesiones del paciente solo de usuario B.

### Fase 5 — Integración frontend

- [ ] `SessionHistoryApiService`: eliminar timer/mock; usar URLs reales + manejo de blob si no aplica.
- [ ] Sustituir `public/mock/session-history.json` por respuesta API (mantener fallback solo en dev si se acuerda).
- [ ] Verificar que panel lateral sigue sin full page reload.

### Fase 6 — Documentación

- [ ] Ejemplo de respuesta lista y detalle en README.
- [ ] Códigos de error para el bloque de reintento de la UI.

---

## 5. Definition of Done

- Paginación **real** desde servidor; orden DESC verificado.
- Detalle por id con estructura acordada y pruebas de permiso.
- Front sin depender de JSON estático para datos de negocio.

---

## 6. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| N+1 al listar nombre paciente | `select_related('patient')` |
| Búsqueda lenta | Índice fulltext o `icontains` acotado + límite de resultados |
| Desalineación page_size | Misma query param que consume Angular |

---

## 7. Dependencias

- **HU-06:** pacientes vinculados.
- **HU-07:** paginación global y formato de error para `listVm`.
- **HU-03 / HU-01:** consumen última sesión; misma fuente de verdad en fechas.

---

## 8. Implementación backend entregada (resumen)

### 8.1 Rutas y contrato

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/sessions/` | Lista paginada, `-occurred_at`, filtros `patientId`, `search`, `ordering`. |
| GET | `/api/v1/sessions/<pk>/` | Detalle con `notes` + `exercises`. |

Convención **404** en detalle si la sesión no está en el queryset del terapeuta (no filtrar existencia entre profesionales). **403** si el usuario no tiene perfil `Therapist`.

### 8.2 Archivos nuevos o actualizados

| Archivo | Rol |
|---------|-----|
| `RehabWeb_API/models.py` | Modelo `SessionExercise` (`session`, `name`, `sets`, `reps`, `notes`, `sort_order`). |
| `RehabWeb_API/filters.py` | `SessionFilter` (`patientId`, `search`). |
| `RehabWeb_API/serializers.py` | `SessionExerciseSerializer`, `SessionListSerializer`, `SessionDetailSerializer` (camelCase). |
| `RehabWeb_API/pagination.py` | `APIPageNumberPagination` (compartido con HU-06 / settings HU-07). |
| `RehabWeb_API/views/sessions.py` | `SessionViewSet` con `APIPageNumberPagination` (`page_size_query_param='page_size'`, máx. 50). |
| `RehabWeb_API/api_urls.py` | `DefaultRouter` + `sessions`. |
| `RehabWeb_API/admin.py` | Inline de ejercicios en `Session`; `SessionExerciseAdmin`. |
| `RehabWeb_API/views/__init__.py` | Export `SessionViewSet`. |
| `RehabWeb_API/tests/test_session_serializers.py` | Forma JSON lista/detalle. |
| `RehabWeb_API/tests/test_sessions_api.py` | 401 / 403. |
| `README.md` | Sección HU-05 y árbol (`filters.py`, `sessions.py`). |

### 8.3 Qué deben hacer los compañeros

1. `makemigrations` / `migrate` para `SessionExercise`.
2. Sembrar sesiones y ejercicios de prueba; verificar filtros y paginación con token.
3. Integrar Angular: lista → `session-list`; panel lateral → `session-detail`.
4. La paginación global DRF (`APIPageNumberPagination`, HU-07) ya aplica a este listado; mantener alineación de `page` / `page_size` con el front.
5. `python manage.py test RehabWeb_API.tests` en local.

### 8.4 Fases del plan — estado

- Fases 1–3 y 6 (doc): cubiertas en código + **§9** (contrato HTTP).
- Fase 4: tests básicos de auth y serializers; ampliar con BD cuando haya migraciones en CI.
- Fase 5: integración front pendiente del equipo.

---

## 9. Apéndice técnico — historial de sesiones

### `GET /api/v1/sessions/`

Token DRF; perfil `Therapist`. Solo sesiones del terapeuta y pacientes con vínculo **activo**. Orden por defecto: `-occurred_at`.

Paginación: `page`, `page_size` (máx. 50). Respuesta: `count`, `next`, `previous`, `results[]` con `id`, `patientId`, `patientName`, `occurredAt`, `programLabel`, `durationMin`, `score`, `status`, `adherencePercent` (lista sin `notes` ni `exercises`).

Filtros: `patientId`, `search` (programa o notas), `ordering` (`occurred_at`, `-occurred_at`, `id`, `-id`).

### `GET /api/v1/sessions/<id>/`

Misma regla de acceso; **404** si la sesión no está en el queryset del terapeuta.

Detalle incluye `notes` y `exercises[]` (`id`, `name`, `sets`, `reps`, `notes`, `sortOrder`).

### Códigos útiles

401 sin auth; 403 sin perfil terapeuta; 404 detalle no autorizado.

### Modelo `SessionExercise`

Tabla hija de `Session`; admin con inline en `Session`.

*Código: `RehabWeb_API/views/sessions.py`, `serializers.py`, `filters.py`.*

---

*Última revisión del plan: 2026-04-23 (secciones 8–9).*
