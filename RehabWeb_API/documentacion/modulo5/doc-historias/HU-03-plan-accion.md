# Plan de acción — HU-03: Alertas proactivas de inactividad

**Propietario sugerido:** Integrante 3  
**Referencias:** Historias HU-03 · Plan backend §Integrante 3 · Reporte front HU-03 · Contrato API (`GET /api/v1/inactivity-alerts/` + management command)

---

## 1. Objetivo de negocio

Detectar pacientes con **más de 3 días** sin sesión registrada, actualizado **al menos una vez al día** por proceso servidor, y mostrar el resultado en **banner del dashboard** y en **`/app/alertas`** con enlace al perfil.

---

## 2. Criterios de aceptación → trazabilidad

| AC | Historias | Front (reporte) | Backend / ops |
|----|-----------|-----------------|---------------|
| AC-01 | Cron diario; diferencia fecha actual − última sesión **más de 3 días** | Copy + tooltips “Job en servidor”; mocks con 5–7 días | `manage.py refresh_inactivity_alerts` (o nombre acordado) + **cron** Linux / Programador de tareas Windows / pipeline cloud |
| AC-02 | Banner amarillo + hipervínculo a perfil | Dashboard + tabla en `/app/alertas`; `patientId` en DTO | API devuelve `patientId` (o UUID) estable y nombre para UI; misma regla **más de 3 días** que el job |

---

## 3. Estado actual

- **Frontend:** `InactivityAlertsDataService`, `INACTIVITY_ALERTS_MOCK`, enlaces a `['/app/pacientes', id]`; dashboard integrado con mock de métricas.
- **Backend:** Sin comando programado ni endpoint; requiere `Session` y `TherapistPatient` con fechas fiables.

---

## 4. Fases de trabajo

### Fase 0 — Regla de negocio exacta

- [ ] Definir “última sesión”: `Session.occurred_at` máximo por paciente **por terapeuta** o global al paciente — **documentar** (afecta multi-terapeuta).
- [ ] Zona horaria: usar `USE_TZ` y fechas conscientes de zona al comparar con “hoy”.
- [ ] Umbral: **estrictamente más de 3 días** (por ejemplo más de 72 h vs más de 3 días calendario) — alinear texto en UI con la implementación.

### Fase 1 — Persistencia de alertas (opcional vs on-the-fly)

**Opción A (recomendada en plan):** tabla `InactivityAlert` materializada por el comando.  
**Opción B:** calcular solo en `GET` (más simple, más carga por request).

- [ ] Elegir A o B y documentar en README.
- [ ] Si A: migraciones + modelo (`patient`, `therapist`, `days_since`, `last_session_at`, `severity`, `updated_at`, etc.).

### Fase 2 — Management command

- [ ] Implementar comando idempotente: recalcula alertas para vínculos **no soft-deleted**.
- [ ] Logging: cuántos pacientes marcados, errores por fila sin abortar todo el batch si se desea.
- [ ] Prueba manual: ejecutar comando dos veces seguidas sin duplicar inconsistencias.

### Fase 3 — API DRF

- [ ] `GET /api/v1/inactivity-alerts/` con autenticación y queryset solo del terapeuta.
- [ ] `django-filter`: por `patientId`, severidad, etc. si producto lo pide.
- [ ] Paginación alineada a HU-07.
- [ ] (Opcional) `PATCH` marcar como vista/dismiss — solo si el front lo implementa.

### Fase 4 — Operaciones

- [ ] README: línea cron ejemplo `0 6 * * * cd /path && venv/bin/python manage.py refresh_inactivity_alerts`.
- [ ] Windows: tarea programada con ruta absoluta al `python.exe` del venv.

### Fase 5 — Tests

- [ ] Unit tests: paciente con sesión hace 2 días → no alerta; hace 4 días → alerta (según definición).
- [ ] API: no expone pacientes ajenos.

### Fase 6 — Integración frontend

- [ ] Reemplazar mock por HTTP; mantener banner y tabla.
- [ ] Ajustar textos de tooltip si el job tiene hora fija real.

---

## 5. Definition of Done

- Proceso **diario** documentado y ejecutable en entorno del curso.
- Criterio **más de 3 días** coincide entre comando, API y mensajes de UI.
- Enlaces del front siguen funcionando con IDs del backend.

---

## 6. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Sin sesiones nunca | Definir si “sin sesión” cuenta como inactivo desde fecha de alta o ignorar |
| Desfase TZ | Una sola política UTC+display |
| Job no instalado en demo | README claro; en desarrollo el comando manual es aceptable si se declara |

---

## 7. Dependencias

- **HU-05 / modelo Session:** fechas y paciente correctos.
- **HU-06:** vínculos `TherapistPatient` y soft delete (excluir desvinculados del cálculo).
- **HU-01:** si el dashboard consume alertas desde dashboard global, misma fuente que esta HU.

---

*Última revisión del plan: 2026-04-23.*
