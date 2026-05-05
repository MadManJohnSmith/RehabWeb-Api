# Contrato API — Endpoints ↔ DTO Angular ↔ capa Django (DRF)

Documento **canónico de alineación** entre el frontend (Angular) y el backend (Django + DRF) del Módulo 5. Las rutas y nombres de serializers son **propuesta inicial**; cualquier cambio debe actualizarse aquí y en el código.

**Referencias:** `Historias de Usuario Modulo 5.md`, `Plan-backend-por-historia-equipo.md`, `Reporte de trabajo frontend.md`.

---

## 1. Convenciones transversales (obligatorio acordar y cumplir)

| Tema | Decisión recomendada | Nota |
|------|----------------------|------|
| Prefijo API | `/api/v1/` | Todas las rutas de producto bajo este prefijo (salvo `GET /health/` si se expone en raíz). |
| JSON | **camelCase** en cuerpos y respuestas | Alinear con DTOs TypeScript; en Django usar `djangorestframework-camel-case` o campos explícitos con `source=`. |
| Autenticación | **DRF Token** (`Authorization: Token <clave>`) | La HU-02 menciona JWT y el front demo muestra `Bearer`; unificar con el stack real o migrar a JWT de forma explícita y documentada. |
| Errores | Formato estándar DRF | `{"detail": "..."}` o errores por campo; documentar códigos HTTP que el Angular ya trata (400, 401, 403, 404, 500). |
| Paginación | `PageNumberPagination` global o por vista | Respuesta con `count`, `next`, `previous`, `results` (o el esquema que se fije y se replique en **todos** los listados). |
| Fechas | ISO 8601 en UTC o `America/Mexico_City` | Una sola política; indicar en cada serializer si es `...Z` o offset. |

---

## 2. Tabla maestra — Endpoint ↔ Front ↔ Backend

| HU | Método y ruta (propuesta) | Artefacto Angular (hoy / objetivo) | Capa Django (propuesta) | Cuerpo / query principal | Respuesta esperada (resumen) |
|----|---------------------------|-------------------------------------|-------------------------|---------------------------|-------------------------------|
| HU-01 | `GET /api/v1/me/dashboard/` | `DashboardDataService.getDashboardMetrics()` · DTO `DashboardMetricsDto` · mock `DASHBOARD_METRICS_MOCK` | Vista `MeDashboardAPIView` o acción `me/dashboard` · serializer `DashboardMetricsSerializer` (solo lectura, nested) | — | JSON equivalente al DTO: alertas resumidas, indicadores, `romByWeek`, serie temporal (meta vs observado), sesiones recientes, metadatos para tooltips / N vs N−1 si el front no recalcula. |
| HU-02 | `POST /api/v1/reports/export/` | `ClinicalExportFiltersDto` · `reports-page.component` · `TherapistSessionService` (cabecera auth) | Vista o `ReportViewSet` · `ClinicalExportRequestSerializer` · permiso “paciente vinculado al terapeuta” | `patientId`, `dateFrom`, `dateTo`, `format`: `pdf` \| `xlsx` | Archivo binario (`Content-Type` + `Content-Disposition`) o job asíncrono acordado. |
| HU-03 | `GET /api/v1/inactivity-alerts/` | `InactivityAlertsDataService.getAlerts()` · `InactivityAlertRowDto` · `INACTIVITY_ALERTS_MOCK` | `InactivityAlertViewSet` (lista) · `InactivityAlertSerializer` · filtros `django-filter` opcionales | `?patientId=`, `?severity=`, paginación | Lista de pacientes inactivos (>3 días desde última sesión), enlazable a `/app/pacientes/:id`. |
| HU-03 | *(proceso)* `python manage.py refresh_inactivity_alerts` | Copy UI “Cron / job servidor” | `ManagementCommand` + tarea programada OS | — | Actualiza tabla `InactivityAlert` o materializa criterio; no es HTTP. |
| HU-04 | `GET /api/v1/patients/{id}/performance-series/` | `ComparisonPerformancePageComponent` · datos desde `patient-detail.mock` / API real | `PatientPerformanceSeriesAPIView` · `PerformanceSeriesSerializer` | — | Series meta vs observado para un paciente (autorizado). |
| HU-04 | `POST /api/v1/performance/compare/` | Vista grupal en comparativa · varios IDs en body | Vista o acción · `PerformanceCompareRequestSerializer` | `{ "patientIds": ["uuid", ...] }` | Objeto por paciente con mismas series o `recoveryScore` semanal según contrato cerrado. |
| HU-05 | `GET /api/v1/sessions/` | `SessionHistoryApiService.searchSessions()` · `session-history.dto.ts` · `sessions-list.mock.ts` | `SessionViewSet` (list) · `SessionListSerializer` · `DjangoFilterBackend` + paginación | `?patientId=`, `?search=`, `?page=`, `?page_size=` | Lista ordenada **desc** por fecha; payload liviano para tabla. |
| HU-05 | `GET /api/v1/sessions/{id}/` | `SessionHistoryApiService.getSessionDetail(id)` · mock `public/mock/session-history.json` | `SessionViewSet` (retrieve) · `SessionDetailSerializer` (notas, ejercicios, adherencia anidados) | — | Detalle para panel lateral sin recargar la página. |
| HU-06 | `GET /api/v1/patients/` | Lista en `patients-list-page` · filas desde `PatientsRegistryService` | `PatientViewSet` o lista de vínculos · `TherapistPatientListSerializer` | `?q=`, `?clinicalStatus=`, `?includeDeleted=` | Tabla: id, identificador asociación, nombre, diagnóstico, estado, última sesión. |
| HU-06 | `POST /api/v1/patients/link/` | Modal vincular en `patients-list-page` | Acción custom o vista · `LinkPatientSerializer` | Identificador externo + datos mínimos paciente | Crea `Patient` + `TherapistPatient`. |
| HU-06 | `PATCH /api/v1/therapist-patients/{id}/` *(o nested)* | Modal editar diagnóstico | Update parcial en vínculo · `TherapistPatientUpdateSerializer` | `primaryDiagnosis`, opcional `clinicalStatus` | Reflejo en lista y ficha. |
| HU-06 | `POST /api/v1/therapist-patients/{id}/unlink/` | Menú desvincular | Acción soft delete · set `deletedAt` | — | 204 o 200 con estado actualizado. |
| HU-06 | `POST /api/v1/therapist-patients/{id}/restore/` | Reactivar en UI | Limpia `deletedAt` si aplica | — | Fila vuelve a activa. |
| HU-06 | `GET /api/v1/patients/{id}/` | `patient-detail-page` · fusión mock + registro | `PatientDetailAPIView` · serializer detalle + métricas si aplica | — | Ficha coherente con lista y comparativa. |
| HU-07 | `GET /api/v1/health/` | *(opcional en Angular)* ping de arranque | Vista mínima + `SELECT 1` | — | `{ "status": "ok" }` y 200. |
| Auth | `POST /api/v1/auth/login/` *(si se expone)* | Flujo real de login Angular | `obtain_auth_token` de DRF o vista custom | `username`, `password` | `{ "token": "..." }` — alinear nombre de campo con el front. |

---

## 3. Mapeo por DTO / archivo front (referencia rápida)

| DTO o tipo (Angular) | Servicio / componente | Endpoint backend al que debe apuntar |
|----------------------|------------------------|--------------------------------------|
| `DashboardMetricsDto` | `DashboardDataService` | `GET /api/v1/me/dashboard/` |
| `ClinicalExportFiltersDto` | `reports-page` + sesión terapeuta | `POST /api/v1/reports/export/` |
| `InactivityAlertRowDto` | `InactivityAlertsDataService` | `GET /api/v1/inactivity-alerts/` |
| Datos comparativa / perfil | `ComparisonPerformancePageComponent`, `patient-detail` | `GET .../performance-series/`, `POST .../performance/compare/`, `GET /api/v1/patients/{id}/` |
| Tipos en `session-history.dto.ts` | `SessionHistoryApiService` | `GET /api/v1/sessions/`, `GET /api/v1/sessions/{id}/` |
| Filas de pacientes (lista) | `PatientsRegistryService` → API | `GET /api/v1/patients/` + acciones link / patch / unlink |

---

## 4. Mapeo por serializer Django (propuesta de nombres en código)

| Serializer (propuesto) | Modelos / fuentes principales | Consumido por (ruta) |
|--------------------------|-------------------------------|----------------------|
| `DashboardMetricsSerializer` | Agregados sobre `MetricPoint`, `Session`, `InactivityAlert` (lectura) | `GET /api/v1/me/dashboard/` |
| `ClinicalExportRequestSerializer` | Validación; no persiste export | `POST /api/v1/reports/export/` |
| `InactivityAlertSerializer` | `InactivityAlert` + datos paciente | `GET /api/v1/inactivity-alerts/` |
| `PerformanceSeriesSerializer` | `MetricPoint` por paciente | `GET /api/v1/patients/{id}/performance-series/` |
| `PerformanceCompareResponseSerializer` | Varios pacientes | `POST /api/v1/performance/compare/` |
| `SessionListSerializer` | `Session` (campos reducidos) | Lista paginada |
| `SessionDetailSerializer` | `Session` + `SessionExercise` nested | Detalle |
| `TherapistPatientListSerializer` | `TherapistPatient` + `Patient` | Lista pacientes del terapeuta |
| `TherapistPatientUpdateSerializer` | `TherapistPatient` | PATCH diagnóstico / estado |
| `LinkPatientSerializer` | Crea `Patient` + `TherapistPatient` | `POST .../link/` |

*(Los nombres exactos pueden variar; lo crítico es que **cada fila de la tabla maestra** siga teniendo un serializer y una vista asignados.)*

---

## 5. Checklist al sustituir mocks

- [ ] Sustituir `DASHBOARD_METRICS_MOCK` por `HttpClient` a `GET /api/v1/me/dashboard/` con el mismo shape de `DashboardMetricsDto` (o adaptar el DTO y el componente en un solo PR).
- [ ] Reportes: dejar de generar CSV en cliente; usar respuesta del `POST` de exportación con token real.
- [ ] Alertas: sustituir `INACTIVITY_ALERTS_MOCK` por `GET /api/v1/inactivity-alerts/`.
- [ ] Historial: eliminar delay + JSON estático; usar `sessions` paginado + retrieve.
- [ ] Pacientes: migrar de `localStorage` a `GET/PATCH/POST` de pacientes y vínculos.
- [ ] Documentar en README cómo obtener el **token DRF** y la URL base (`environment.ts`).

---

## 6. Historial de cambios del contrato

| Fecha | Cambio |
|-------|--------|
| 2026-04-23 | Creación inicial del documento a partir del plan backend y del reporte frontend. |

*Mantener este archivo actualizado cuando cambie cualquier ruta, nombre de campo JSON o estrategia de autenticación.*
