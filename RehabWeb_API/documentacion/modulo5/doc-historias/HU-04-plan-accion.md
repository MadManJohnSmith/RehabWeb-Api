# Plan de acción — HU-04: Comparativa de desempeño (individual y grupal)

**Propietario sugerido:** Integrante 4  
**Referencias:** Historias HU-04 · Plan backend §Integrante 4 · Reporte front HU-04 · Contrato API (`performance-series`, `performance/compare`)

---

## 1. Objetivo de negocio

Comparar **desempeño real** frente a **meta inicial** para ajustar planes: vista **individual** y **grupal** con varios pacientes en una sola gráfica (`/app/comparativa`).

---

## 2. Criterios de aceptación → trazabilidad

| AC | Historias | Front (reporte) | Backend |
|----|-----------|-----------------|---------|
| AC-01 | Superposición meta vs real; fórmula de progreso en figura | Texto de fórmula en UI; gráficos SVG; datos de `patient-detail.mock` | `MetricPoint` (o similar) con `meta_value` / `observed_value`; **función pura** Python para progreso \(M0, M*, R\) + **tests unitarios**; subir imagen `image-20260311-233530.png` al repo o transcribir fórmula en código y docs |
| AC-02 | Multi-selección; Recovery Scores comparativos en una interfaz | Vista grupal con varios pacientes; `groupBounds`; leyenda por color | `POST /api/v1/performance/compare/` con lista de IDs validada; máximo de pacientes por request; respuesta por paciente con series alineadas temporalmente |

---

## 3. Estado actual

- **Frontend:** `ComparisonPerformancePageComponent`, ruta `comparativa`, mocks compartidos con ficha paciente.
- **Backend:** Endpoints y modelo de métricas por implementar; permisos “solo mis pacientes”.

---

## 4. Fases de trabajo

### Fase 0 — Congelar fórmula y contrato

- [ ] Obtener definición exacta de la figura en `Historias de Usuario Modulo 5.md` (imagen en repo).
- [ ] Escribir la fórmula en Markdown técnico + casos borde (división por cero, valores faltantes).
- [ ] Acordar unidad temporal de la serie (semana calendario vs sesión).

### Fase 1 — Modelo y datos

- [ ] `MetricPoint` con FK paciente, tipo, periodo, meta, observado.
- [ ] Índices para consultas por lista de `patient_ids` + rango de periodos.
- [ ] Semillas con curvas que el front pueda graficar sin reescalar manualmente raro.

### Fase 2 — API individual

- [ ] `GET /api/v1/patients/{id}/performance-series/` — 404 si paciente no existe o no está vinculado al terapeuta.
- [ ] `PerformanceSeriesSerializer`: lista ordenada de puntos con metadatos para tooltips.

### Fase 3 — API grupal

- [ ] `POST /api/v1/performance/compare/` — validar duplicados, máximo N pacientes, todos autorizados.
- [ ] Respuesta: diccionario/lista por `patientId` con series y opcionalmente `recoveryScore` calculado server-side.

### Fase 4 — Tests

- [ ] Tests unitarios de la función de fórmula (tabla de ejemplos manuales).
- [ ] Tests API: 403 mezclando ID ajeno; 400 lista vacía o demasiado larga.

### Fase 5 — Integración frontend

- [ ] Sustituir mocks por servicios HTTP en vista individual y grupal.
- [ ] Mantener leyenda/colores; ajustar si el backend devuelve nombres de series distintos.

### Fase 6 — Documentación

- [ ] Ejemplos JSON en README o OpenAPI.
- [ ] Referencia cruzada a imagen de fórmula en documentación de módulo.

---

## 5. Definition of Done

- Fórmula **probada** y trazable al documento de HU.
- Endpoints individuales y de comparativa con permisos correctos.
- Front consume API en ambas vistas sin depender de `PATIENT_DETAIL_MOCK` para series de desempeño.

---

## 6. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Imagen de fórmula ausente | Bloquear Fase 0 hasta tener spec escrita firmada por PO |
| Escalas distintas entre pacientes | API puede devolver min/max sugeridos o front mantiene `groupBounds` con datos crudos |
| Duplicación con HU-01 | Reutilizar queryset/helper de métricas; DRY en servicio `metrics_service.py` |

---

## 7. Dependencias

- **HU-06:** autorización por paciente.
- **HU-07:** convención JSON y errores.
- **HU-01:** mismo modelo `MetricPoint` si se comparte dashboard (diseño conjunto).

---

*Última revisión del plan: 2026-04-23.*
