# Contrato API — Endpoints ↔ DTO Angular ↔ capa Django (DRF)

Documento **canónico de alineación** entre el frontend (Angular) y el backend (Django + DRF) del Módulo 5. Las rutas y nombres de serializers son **propuesta inicial**; cualquier cambio debe actualizarse aquí y en el código.

**Referencias:** `Historias de Usuario Modulo 5.md`, `Plan-backend-por-historia-equipo.md`, `Reporte de trabajo frontend.md`.

---

## 1. Convenciones transversales (obligatorio acordar y cumplir)

| Tema | Decisión recomendada | Nota |
|------|----------------------|------|
| Prefijo API | `/api/v1/` | Incluye `GET /api/v1/health/` (sin auth). |
| JSON | **camelCase** en cuerpos y respuestas | Alinear con DTOs TypeScript; en Django usar `djangorestframework-camel-case` o campos explícitos con `source=`. |
| Autenticación | **DRF Token** (`Authorization: Token <clave>`) | **Decisión HU-07:** stack canónico = Token DRF + `POST /api/v1/auth/login/` y `POST /api/v1/auth/logout/`; no `Bearer` salvo migración explícita a JWT documentada en este archivo. |
| Errores | Formato estándar DRF | `{"detail": "..."}` o errores por campo; documentar códigos HTTP que el Angular ya trata (400, 401, 403, 404, 500). |
| Paginación | `APIPageNumberPagination` (global DRF) | `page` + `page_size` (máx. 50); respuesta `count`, `next`, `previous`, `results` en listados paginados. Objetos compuestos (dashboard, alertas) sin ese envoltorio. |
| Fechas | ISO 8601 en UTC o `America/Mexico_City` | Una sola política; indicar en cada serializer si es `...Z` o offset. |

---

## 2. Tabla maestra — Endpoint ↔ Front ↔ Backend

| HU | Método y ruta (propuesta) | Artefacto Angular (hoy / objetivo) | Capa Django (propuesta) | Cuerpo / query principal | Respuesta esperada (resumen) |
|----|---------------------------|-------------------------------------|-------------------------|---------------------------|-------------------------------|
| HU-01 | `GET /api/v1/me/dashboard/` | `DashboardDataService.getDashboardMetrics()` · DTO `DashboardMetricsDto` · mock `DASHBOARD_METRICS_MOCK` | Vista `MeDashboardAPIView` o acción `me/dashboard` · serializer `DashboardMetricsSerializer` (solo lectura, nested) | — | JSON equivalente al DTO: alertas resumidas, indicadores, `romByWeek`, serie temporal (meta vs observado), sesiones recientes, metadatos para tooltips / N vs N−1 si el front no recalcula. |
| HU-02 | `POST /api/v1/reports/export/` | `ClinicalExportApiRequestDto` · `ClinicalExportApiService` · `reports-page.component` · interceptor `Authorization: Token …` | `ReportExportAPIView` · `ClinicalExportRequestSerializer` · permiso “paciente vinculado al terapeuta” | `patientId` (**int**), `dateFrom`, `dateTo`, `format`: `pdf` \| `xlsx` | Archivo binario (`Content-Type` + `Content-Disposition`). |
| HU-03 | `GET /api/v1/inactivity-alerts/` | `InactivityAlertsDataService.getAlertsView()` · mapper · `InactivityAlertsViewDto` · respaldo `INACTIVITY_ALERTS_MOCK_VIEW` | `InactivityAlertListAPIView` · datos en vivo (`get_inactive_patients_for_therapist`) | `?patientId=` (opcional, entero) | `{ thresholdDays, inactiveCount, alerts[] }` con `patientId`, `fullName`, `daysSinceLastSession`, `lastSessionAt`; prioridad UI calculada en front. |
| HU-03 | *(proceso)* `python manage.py refresh_inactivity_alerts` | Copy UI “Cron / job servidor” | `ManagementCommand` + tarea programada OS | — | Actualiza tabla `InactivityAlert` o materializa criterio; no es HTTP. |
| HU-04 | `GET /api/v1/patients/{id}/performance-series/` | *(Opcional)* ficha / gráficos por paciente | `PatientPerformanceSeriesAPIView` | — | Serie temporal meta vs observado (`temporalSeries`, `summary`). |
| HU-04 | `POST /api/v1/performance/compare/` | `PerformanceCompareApiService` · `ComparisonPerformancePageComponent` · tipos `performance-compare-api.types.ts` | `PerformanceCompareAPIView` · `PerformanceCompareRequestSerializer` | `{ "patientIds": [1, 2, ...] }` (**enteros**, máx. 12) | `{ patients[], groupBounds }` · cada paciente: `patientId`, `fullName`, `temporalSeries`, `summary`. |
| HU-05 | `GET /api/v1/sessions/` | `SessionHistoryApiService.searchSessions()` · `session-history.dto.ts` | `SessionViewSet` (list) · `SessionListSerializer` · filtros + paginación | `?patientId=`, `?search=`, `?page=`, `?page_size=` | Lista paginada DRF (`count`, `next`, `previous`, `results`). |
| HU-05 | `GET /api/v1/sessions/{id}/` | `SessionHistoryApiService.getSessionDetail(id)` | `SessionViewSet` (retrieve) · `SessionDetailSerializer` | — | Detalle para panel lateral. |
| HU-06 | `GET /api/v1/patients/` | `PatientsApiService.list()` · `patients-list-page` | `TherapistPatientListAPIView` · `TherapistPatientRowSerializer` | `?q=`, `?clinicalStatus=`, `?includeDeleted=`, `page`, `page_size` | Tabla con `patientId` numérico, vínculo, diagnóstico, estado, última sesión. |
| HU-06 | `POST /api/v1/patients/link/` | Modal vincular en `patients-list-page` | Acción custom o vista · `LinkPatientSerializer` | Identificador externo + datos mínimos paciente | Crea `Patient` + `TherapistPatient`. |
| HU-06 | `PATCH /api/v1/therapist-patients/{id}/` *(o nested)* | Modal editar diagnóstico | Update parcial en vínculo · `TherapistPatientUpdateSerializer` | `primaryDiagnosis`, opcional `clinicalStatus` | Reflejo en lista y ficha. |
| HU-06 | `POST /api/v1/therapist-patients/{id}/unlink/` | Menú desvincular | Acción soft delete · set `deletedAt` | — | 204 o 200 con estado actualizado. |
| HU-06 | `POST /api/v1/therapist-patients/{id}/restore/` | Reactivar en UI | Limpia `deletedAt` si aplica | — | Fila vuelve a activa. |
| HU-06 | `GET /api/v1/patients/{id}/` | `patient-detail-page` · fusión mock + registro | `PatientDetailAPIView` · serializer detalle + métricas si aplica | — | Ficha coherente con lista y comparativa. |
| HU-07 | `GET /api/v1/health/` | *(opcional en Angular)* ping de arranque | `HealthAPIView` + `SELECT 1` | — | `{ "status": "ok" }` y 200; `503` si la BD no responde. |
| Auth | `POST /api/v1/auth/login/` | Login Angular / interceptor | `obtain_auth_token` (DRF) | `username`, `password` | `{ "token": "..." }`. |
| Auth | `POST /api/v1/auth/logout/` | Cierre de sesión (invalidar token) | `LogoutAPIView` | — | `204` sin cuerpo. |

---

## 3. Mapeo por DTO / archivo front (referencia rápida)

| DTO o tipo (Angular) | Servicio / componente | Endpoint backend al que debe apuntar |
|----------------------|------------------------|--------------------------------------|
| `DashboardMetricsDto` | `DashboardDataService` | `GET /api/v1/me/dashboard/` |
| `ClinicalExportApiRequestDto` | `ClinicalExportApiService` · `reports-page` | `POST /api/v1/reports/export/` |
| `InactivityAlertsViewDto` / `InactivityAlertRowDto` | `InactivityAlertsDataService` + mapper | `GET /api/v1/inactivity-alerts/` |
| `PerformanceCompareApiResponse` | `PerformanceCompareApiService` · comparativa | `POST /api/v1/performance/compare/` |
| Tipos en `session-history.dto.ts` | `SessionHistoryApiService` | `GET /api/v1/sessions/`, `GET /api/v1/sessions/{id}/` |
| Filas de pacientes (lista) | `PatientsApiService` | `GET /api/v1/patients/` + link / patch / unlink / restore |
| `patient-detail-page` | Mock local + API donde aplique | `GET /api/v1/patients/{id}/` (ficha) |

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
| `TherapistPatientRowSerializer` | `TherapistPatient` + `Patient` + `last_session_at` | Lista, ficha, respuestas de link / patch / unlink / restore |
| `TherapistPatientPatchSerializer` | Validación parcial | `PATCH .../therapist-patients/{id}/` |
| `PatientLinkRequestSerializer` | Crea o reutiliza `Patient` + `TherapistPatient` | `POST .../patients/link/` |

*(Los nombres exactos pueden variar; lo crítico es que **cada fila de la tabla maestra** siga teniendo un serializer y una vista asignados.)*

---

## 5. Checklist al sustituir mocks

- [x] Dashboard: `DashboardDataService` + `mapDashboardApiToDto` → `GET /api/v1/me/dashboard/` (respaldo mock en error).
- [x] Reportes: `ClinicalExportApiService` + `Blob` / `POST /api/v1/reports/export/` con token DRF.
- [x] Alertas: `GET /api/v1/inactivity-alerts/` + mapper (respaldo mock en error).
- [x] Historial: `SessionHistoryApiService` → `GET /api/v1/sessions/` + detalle.
- [x] Pacientes: `PatientsApiService` → lista/ficha/link/PATCH/unlink/restore.
- [x] Comparativa: `POST /api/v1/performance/compare/` integrado en Angular.
- [x] README WebApp: URL base, token DRF, orden de arranque; tests unitarios de mappers y `AuthService` (ver repo `RehabWeb-WebApp`).

---

## 6. Historial de cambios del contrato

| Fecha | Cambio |
|-------|--------|
| 2026-04-23 | Creación inicial del documento a partir del plan backend y del reporte frontend. |
| 2026-04-23 | HU-06: nombres de serializers alineados (`TherapistPatientRowSerializer`, `PatientLinkRequestSerializer`, `TherapistPatientPatchSerializer`). |
| 2026-04-23 | HU-07: auth login/logout, health bajo `/api/v1/`, paginación global `APIPageNumberPagination`, decisión Token DRF explícita. |
| 2026-05-12 | Alineación RehabWeb-WebApp: tabla maestra §2 y §3 actualizadas (export, alertas, sesiones, pacientes, comparativa); checklist §5 marcado según integración real; `patientIds` en compare como **array de enteros**. |

*Mantener este archivo actualizado cuando cambie cualquier ruta, nombre de campo JSON o estrategia de autenticación.*
