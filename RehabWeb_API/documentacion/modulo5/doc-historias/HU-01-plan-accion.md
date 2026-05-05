# Plan de acción — HU-01: Dashboard de progreso visual

**Propietario sugerido (plan equipo):** Integrante 1  
**Referencias:** Historias Módulo 5 · Plan backend §Integrante 1 · Reporte front HU-01 · Contrato API (`GET /api/v1/me/dashboard/`)

---

## 1. Objetivo de negocio

El terapeuta identifica **tendencias de recuperación** con gráficas (ROM semanal, serie temporal meta vs observado) y contexto de sesiones/alertas en un solo tablero (`/app`).

---

## 2. Criterios de aceptación (producto) → responsable

| AC | Texto (historias) | Front (reporte) | Backend |
|----|---------------------|-----------------|---------|
| AC-01 | Consultas a tablas de métricas + JSON para ROM y series | Mock `DASHBOARD_METRICS_MOCK`; `romByWeek`; serie temporal | Consultas reales a `MetricPoint` / `Session` (u orm agregado); serializer alineado a `DashboardMetricsDto` |
| AC-02 | Mouseover, colores verde/rojo según N vs N−1 | Implementado en UI (`dotsNvNMinus1` sobre `observedValue`) | Opción A: devolver solo valores y el front mantiene lógica. Opción B: backend precalcula `trend` por punto para consistencia multi-cliente — **acordar en contrato** |
| AC-03 | Carga + render en menos de 3 s | Datasets demo acotados; nota en UI | `annotate`/índices/`only()`, límite de ventana temporal, `select_related`; medición con datos realistas; caché opcional por terapeuta |

---

## 3. Estado actual

- **Frontend:** `DashboardPageComponent`, `DashboardDataService.getDashboardMetrics()`, señales con mock; shell/scroll ya corregidos. Pendiente: cablear `HttpClient` al JSON real del endpoint.
- **Backend:** implementado `GET /api/v1/me/dashboard/` (ver sección 8). Modelos en `models.py`; las **migraciones** y datos de prueba los aplica el equipo al levantar el servidor.

---

## 4. Fases de trabajo

### Fase 0 — Discovery (0.5–1 d)

- [ ] Congelar **JSON de ejemplo** exportado del mock actual (`DashboardMetricsDto`) como fixture de contrato.
- [ ] Acordar con front: **¿tendencia N vs N−1 en servidor o cliente?** y documentar en `Contrato-API-endpoints-DTO-serializers.md`.
- [ ] Definir ventana máxima (p. ej. últimas N semanas) para cumplir AC-03.

### Fase 1 — Modelo y datos (bloquea con HU-04)

- [ ] Confirmar esquema `MetricPoint` (o tabla equivalente): paciente, tipo métrica, periodo, `meta_value`, `observed_value`, timestamps.
- [ ] Índices MySQL: por `(patient_id, period)` o según consultas del dashboard.
- [ ] Semillas: datos coherentes con gráficas del mock (mismas magnitudes aproximadas).

### Fase 2 — API Django/DRF

- [ ] Implementar `GET /api/v1/me/dashboard/` con `IsAuthenticated`.
- [ ] `get_queryset`/servicio interno: **solo pacientes vinculados** al `request.user` (vía `TherapistPatient`, dependencia HU-06).
- [ ] `DashboardMetricsSerializer` (nested): ROM, serie temporal, resumen alertas (puede leer de misma fuente que HU-03 o agregado liviano), sesiones recientes (lectura de `Session` ordenada).
- [ ] Evitar N+1 queries; perfilar con `django-debug-toolbar` o logging de query count en desarrollo.

### Fase 3 — Calidad y seguridad

- [ ] Tests: `APITestCase` — 401 sin token; 200 con token; forma JSON clave mínima; no filtra pacientes ajenos.
- [ ] Test de rendimiento **smoke** (opcional): tiempo de vista bajo umbral acordado con dataset mediano en CI o local documentado.

### Fase 4 — Integración frontend

- [ ] `DashboardDataService`: conmutar de mock a `HttpClient` + `environment.apiUrl`.
- [ ] Manejo de vacío: si no hay métricas, UI en estado controlado (alineado HU-07 AC-03).
- [ ] Verificar tooltips y colores con payload real.

### Fase 5 — Documentación y operación

- [ ] README: ejemplo `curl` con `Authorization: Token …`.
- [ ] Actualizar contrato si cambian nombres de campos.

---

## 5. Definition of Done (DoD)

- Los **AC de historias** quedan cubiertos o explícitamente repartidos (AC-02 en front vs back documentado).
- Endpoint estable bajo `/api/v1/` con permisos correctos.
- Tests mínimos verdes; sin datos sensibles en fixtures.

---

## 6. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Dashboard lento con muchos pacientes | Límite de ventana, agregados en BD, caché corto, snapshot opcional |
| JSON distinto al mock | Contrato + PR conjunto front/back o adaptador en serializer |
| HU-06 atrasada | Mock temporal solo en front **no** sustituye; backend puede usar usuario staff con datos semilla para desarrollo |

---

## 7. Dependencias

- **HU-07:** rutas versionadas, auth, CORS, paginación global si aplica a otras vistas.
- **HU-06:** vínculo terapeuta–paciente para filtrar datos.
- **HU-05 / HU-03:** sesiones recientes y conteo alertas; alinear fuentes para no duplicar lógica contradictoria.

---

## 8. Implementación backend entregada (resumen)

Esta sección documenta lo ya construido en código para que el equipo **pulir**, **migrar**, **probar en local** y alinear con el mock de Angular.

### 8.1 Archivos nuevos o actualizados

| Archivo | Rol |
|---------|-----|
| `RehabWeb_API/api_urls.py` | Ruta `me/dashboard/` → `MeDashboardAPIView`. |
| `RehabWeb_API/services/dashboard_metrics.py` | `build_dashboard_payload(user)`: resuelve `Therapist`, vínculos activos (`TherapistPatient` sin `deleted_at`), agrega ROM y serie temporal desde `MetricPoint` (promedio por periodo si hay varios pacientes), sesiones recientes, inactividad (misma idea que HU-03: más de 3 días desde la última sesión o sin sesión), tendencias N vs N−1 (`initial` / `improved` / `regressed` / `unchanged`), tope de filas de métricas para AC-03, y `summaryRings` básicos. |
| `RehabWeb_API/views/dashboard.py` | `GET` autenticado → JSON **camelCase**. |
| `RehabWeb_API/services/__init__.py` | Paquete de servicios. |
| `RehabWeb_API/tests/test_dashboard_metrics.py` | Pruebas **sin ORM** de agregación y tendencias. |
| `RehabWeb_API/tests/test_dashboard_api.py` | 401 sin token; 200 con token **mockeando** `build_dashboard_payload` (no exige migraciones de las tablas del app para ese caso). |
| `README.md` | Eliminado el comando inexistente `seed_module5_demo`; aclaración de que deben **migrar** y crear `Therapist` + datos; árbol del proyecto sin migración `0001` inventada. |
| `RehabWeb_API/urls.py` | Ya incluía `api/v1/`; con `api_urls.py` queda enlazado. |

### 8.2 Qué deben hacer los compañeros (checklist)

1. Ejecutar `python manage.py makemigrations` y `migrate` (MySQL en desarrollo, o SQLite en memoria al correr tests, según `settings.py`).
2. Crear `User` + `Therapist` (relación 1:1) + `Patient` / `TherapistPatient` / `Session` / `MetricPoint` (vía admin Django, fixtures o comando seed que el equipo defina).
3. Probar con **token DRF** y `curl` como en el `README.md` del repositorio.
4. Ajustar el **frontend** para consumir este JSON si difiere del mock; referencia de campos: **§9** de este plan.
5. En máquina local del desarrollador: `python manage.py test RehabWeb_API.tests` (en entornos CI sin Python configurado en PATH, ejecutar los tests solo en local).

### 8.3 Notas de alineación producto ↔ backend

- **AC-02:** el backend devuelve `trend` por punto en `temporalSeries`; el front puede seguir calculando colores o preferir estos tokens — documentar la decisión final en `Contrato-API-endpoints-DTO-serializers.md` si cambia.
- **AC-03:** el tope de filas de `MetricPoint` acota la respuesta; medir con datos reales tras migrar.

---

## 9. Apéndice técnico — esquema JSON `GET /api/v1/me/dashboard/`

Respuesta en **camelCase** (sin `djangorestframework-camel-case`).

### Raíz

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `therapistLinked` | boolean | `false` si el `User` no tiene fila en `Therapist`; el front puede mostrar aviso o flujo de alta. |
| `inactivitySummary` | object | Resumen para banner amarillo (HU-03); misma regla de tiempo que el job futuro. |
| `romByWeek` | array | Puntos ROM semanal agregados (promedio por periodo si hay varios pacientes). |
| `temporalSeries` | array | Serie temporal meta/observado + `trend` por punto. |
| `recentSessions` | array | Últimas sesiones del terapeuta (solo pacientes vinculados activos). |
| `summaryRings` | array | KPIs simples (conteos / medias) para anillos o tarjetas. |

### `inactivitySummary`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `inactiveCount` | int | Número de pacientes inactivos según umbral. |
| `thresholdDays` | int | Siempre `3` (referencia de producto; la comparación real usa `timedelta(days=3)` sobre la última sesión). |
| `patients` | array | Cada elemento: `patientId`, `fullName`, `daysSinceLastSession` (nullable), `lastSessionAt` (ISO8601 o `null`). |

Inactividad: última sesión ausente **o** `(ahora - última sesión) > 3 días`.

### `romByWeek` / puntos de serie

| Campo | Tipo |
|-------|------|
| `sortOrder` | int |
| `periodLabel` | string |
| `metaValue` | number (float) |
| `observedValue` | number (float) |

### `temporalSeries`

Igual que arriba más:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `trend` | string | `initial` \| `improved` \| `regressed` \| `unchanged` (N vs N−1 sobre `observedValue`). |

### `recentSessions`

| Campo | Tipo |
|-------|------|
| `id` | int |
| `patientId` | int |
| `patientName` | string |
| `occurredAt` | string (ISO8601) |
| `programLabel` | string |
| `durationMin` | int \| null |
| `score` | number \| null |
| `status` | string |
| `adherencePercent` | int \| null |

### `summaryRings`

| Campo | Tipo |
|-------|------|
| `key` | string |
| `label` | string |
| `value` | number |
| `maxValue` | number |
| `unit` | string (`count`, `percent`, …) |

*Alineado con `RehabWeb_API/services/dashboard_metrics.py`. Si el DTO Angular difiere, actualizar este apéndice y el servicio en un solo cambio.*

---

*Última revisión del plan: 2026-04-23 (secciones 8–9: implementación y apéndice técnico).*
