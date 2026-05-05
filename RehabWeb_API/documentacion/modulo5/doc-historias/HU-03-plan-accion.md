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

- **Frontend:** `InactivityAlertsDataService`, `INACTIVITY_ALERTS_MOCK`, enlaces a `['/app/pacientes', id]`; dashboard integrado con mock de métricas. Pendiente: consumir `GET /api/v1/inactivity-alerts/` (y/o el bloque del dashboard ya alineado con backend).
- **Backend:** comando `refresh_inactivity_alerts`, modelo `InactivityAlert`, API listado y reglas compartidas con HU-01 (ver sección 8). Migraciones: a cargo del equipo.

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

## 8. Implementación backend entregada (resumen)

### 8.1 Regla y arquitectura

| Tema | Decisión |
|------|----------|
| Última sesión | `Session.occurred_at` máx. por **(terapeuta, paciente)**. |
| Umbral | `timedelta(days=3)` — más de 72 h sin sesión ⇒ inactivo. |
| Sin sesiones | Cuenta como inactivo (`severity` `no_sessions` en tabla). |
| API vs tabla | **GET** devuelve lista **en vivo** (`get_inactive_patients_for_therapist`); el **comando** actualiza **`InactivityAlert`** para AC-01 y auditoría. |
| Dashboard HU-01 | Usa la misma función para `inactivitySummary.patients`. |

### 8.2 Archivos nuevos o actualizados

| Archivo | Rol |
|---------|-----|
| `RehabWeb_API/models.py` | Modelo `InactivityAlert`. |
| `RehabWeb_API/services/inactivity_rules.py` | `INACTIVITY_THRESHOLD`, `get_inactive_patients_for_therapist`, `last_session_times_by_patient`. |
| `RehabWeb_API/services/inactivity_sync.py` | `sync_inactivity_alerts_for_therapist`, `sync_all_inactivity_alerts`. |
| `RehabWeb_API/services/dashboard_metrics.py` | Delega inactividad en `inactivity_rules` (sin duplicar lógica). |
| `RehabWeb_API/views/inactivity.py` | `InactivityAlertListAPIView` → `GET /api/v1/inactivity-alerts/`. |
| `RehabWeb_API/api_urls.py` | Ruta `inactivity-alerts/`. |
| `RehabWeb_API/management/commands/refresh_inactivity_alerts.py` | Job batch documentado para cron. |
| `RehabWeb_API/admin.py` | Registro de `InactivityAlert`. |
| `RehabWeb_API/views/__init__.py` | Export de la nueva vista. |
| `RehabWeb_API/tests/test_inactivity_rules.py` | Umbral temporal. |
| `RehabWeb_API/tests/test_inactivity_api.py` | 401 / 403 / 200 con mocks. |
| `RehabWeb_API/tests/test_refresh_inactivity_command.py` | Smoke del comando. |
| `README.md` | Sección HU-03 (si se añadió en el mismo PR). |

### 8.3 Qué deben hacer los compañeros

1. `makemigrations` / `migrate` para `InactivityAlert`.
2. Datos: `Therapist`, vínculos activos, `Session` con fechas coherentes.
3. Probar `GET /api/v1/inactivity-alerts/` con token; opcional `?patientId=`.
4. Ejecutar `python manage.py refresh_inactivity_alerts` y revisar filas en admin.
5. Programar cron o tarea programada en el entorno del curso.
6. Integrar el front sustituyendo mocks por `HttpClient`.
7. `python manage.py test RehabWeb_API.tests` en local.

### 8.4 Fases del plan — estado

- **Fase 0:** reglas y contrato HTTP en **§9** de este plan.
- **Fase 1:** Opción A (`InactivityAlert`) implementada; API en vivo no exige filas previas.
- **Fase 2–4:** comando + README/cron en doc y README raíz.
- **Fase 5:** tests añadidos (integración ORM ampliable cuando existan migraciones).
- **PATCH “visto”:** no implementado (front no lo pedía).

---

## 9. Apéndice técnico — alertas de inactividad

### Regla de negocio (código)

- Archivo: `RehabWeb_API/services/inactivity_rules.py`.
- **Última sesión:** máximo `Session.occurred_at` por par **(terapeuta, paciente)**.
- **Inactivo:** no hay sesiones **o** `(ahora - última sesión) > timedelta(days=3)`.
- Sin sesiones nunca registradas: se considera **inactivo** (`daysSinceLastSession` puede ser `null` en JSON).

El **dashboard** (HU-01) usa la misma función `get_inactive_patients_for_therapist` para `inactivitySummary`.

### `GET /api/v1/inactivity-alerts/`

- Autenticación: token DRF; requiere fila `Therapist`. Respuesta **en vivo**.

| Parámetro (query) | Descripción |
|-------------------|-------------|
| `patientId` | Filtra a ese ID (entero). |

Ejemplo de cuerpo (200): `thresholdDays`, `inactiveCount`, `alerts[]` con `patientId`, `fullName`, `daysSinceLastSession`, `lastSessionAt`. Códigos: 401, 403, 400 si `patientId` no entero.

### Comando `refresh_inactivity_alerts`

Materializa `InactivityAlert` para el job diario:

```bash
python manage.py refresh_inactivity_alerts
```

Cron (Linux) ejemplo: `0 6 * * * cd /ruta/RehabWeb-Api && .venv/bin/python manage.py refresh_inactivity_alerts`. Windows: Programador de tareas con el `python` del venv.

### Modelo `InactivityAlert`

Campos principales: `therapist`, `patient`, `days_since_last_session`, `last_session_at`, `severity` (`low` / `medium` / `high` / `no_sessions`), `updated_at`.

---

*Última revisión del plan: 2026-04-23 (secciones 8–9).*
