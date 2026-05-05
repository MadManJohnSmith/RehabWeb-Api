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

- **Frontend:** `DashboardPageComponent`, `DashboardDataService.getDashboardMetrics()`, señales con mock; shell/scroll ya corregidos.
- **Backend:** API aún no expuesta en código; modelos métricos por definir/migrar.

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

*Última revisión del plan: 2026-04-23.*
