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

- **Frontend:** `session-history-page`, `toSignal` + `combineLatest` + `switchMap`; estados **carga / error / vacío** y reintento (HU-07 alineado).
- **Backend:** Modelos `Session`, `SessionExercise`, notas por definir; sin vistas DRF expuestas.

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

*Última revisión del plan: 2026-04-23.*
