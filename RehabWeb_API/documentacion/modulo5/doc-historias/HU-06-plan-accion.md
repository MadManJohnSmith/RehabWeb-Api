# Plan de acción — HU-06: Gestión y asociación de pacientes (CRUD)

**Propietario sugerido:** Integrante 6  
**Referencias:** Historias HU-06 · Plan backend §Integrante 6 · Reporte front HU-06 · Contrato API (pacientes, link, patch, unlink, restore, detalle)

---

## 1. Objetivo de negocio

Administrar **lista de pacientes activos** del terapeuta: búsqueda, **vinculación** por identificador único, **edición** de diagnóstico desde lista, **borrado lógico** al desvincular, **reactivación**, e indicador de estado **Riesgo / Activo / Alta** (`/app/pacientes`, ficha `/app/pacientes/:id`).

---

## 2. Criterios de aceptación → trazabilidad

| AC | Historias | Front (reporte) | Backend |
|----|-----------|-----------------|---------|
| AC-01 | Búsqueda y vinculación 1:N terapeuta–paciente | Modal vincular; `PatientsRegistryService.linkPatient`; seed desde mock | `POST .../patients/link/` crea o reutiliza `Patient` + `TherapistPatient`; validación de **identificador único** (externo o interno); búsqueda `GET` con `q` |
| AC-02 | Edición diagnóstico en lista; soft delete desde menú | Modales; `updateCondition`; `unlink` atenúa fila “Desvinculado”; `restore` | `PATCH` en vínculo; `POST .../unlink/` setea `deleted_at`; `restore` limpia soft delete; reglas en serializers |
| AC-03 | Estado Riesgo / Activo / Alta | Colores en tabla y ficha | `clinical_status` en modelo con choices; validar transiciones si aplica |

---

## 3. Estado actual

- **Frontend:** `patients-list-page`, `patient-detail-page`, menú ⋮, `localStorage` vía `PatientsRegistryService` (migrar a API).
- **Backend:** Modelos `Patient` / `TherapistPatient` y endpoints HU-06 (lista, ficha, link, PATCH, unlink, restore); ver sección 8.

---

## 4. Fases de trabajo

### Fase 0 — Modelado relacional

- [x] Modelo `Therapist` 1:1 con `User`; `Patient` (`external_id`, `full_name`); `TherapistPatient` con `primary_diagnosis`, `clinical_status`, `deleted_at` y restricción única de vínculo activo.
- [x] Índices acordados en `TherapistPatient`.

### Fase 1 — Migraciones y admin

- [ ] `makemigrations` / `migrate` en `rehab_db`.
- [ ] (Opcional) Registro en Django Admin solo staff para soporte.

### Fase 2 — API lista y detalle

- [x] `GET /api/v1/patients/` — queryset de vínculos del usuario; query `includeDeleted`, `clinicalStatus`, `q`.
- [x] Respuesta alineada a columnas de tabla: id, identificador asociación, nombre, diagnóstico, estado, última sesión (subquery o annotate desde `Session` — coordinar con HU-05).
- [x] `GET /api/v1/patients/{id}/` — detalle para ficha y rutas de comparativa.

### Fase 3 — Mutaciones

- [x] `POST /api/v1/patients/link/` — política: mismo terapeuta puede actualizar vínculo activo; otro terapeuta con mismo `Patient` (por `external_id`) → **409**; sin `associationId` siempre se crea un `Patient` nuevo (`external_id` vacío).
- [x] `PATCH` diagnóstico y/o estado.
- [x] `POST .../unlink/` y `.../restore/` con respuestas coherentes para que la UI actualice fila sin `localStorage`.

### Fase 4 — Tests

- [x] Flujo: crear usuario terapeuta + token; link; listar; patch; unlink lista atenuada; restore.
- [x] Intento de acceso a paciente ajeno → 404 en ficha; **403** sin perfil terapeuta (lista).

### Fase 5 — Integración frontend

- [ ] Migrar `PatientsRegistryService` a API: inicialización desde `GET`, persistencia en servidor.
- [ ] Eliminar o reducir `localStorage` a caché opcional offline (solo si se acuerda).
- [ ] Asegurar que **ficha** y **comparativa** leen el mismo detalle/API tras edición.

### Fase 6 — Documentación y semillas

- [ ] Comando `seed_demo` o fixture: terapeuta, 3–5 pacientes, estados mixtos, algunos soft-deleted.
- [ ] README: flujo de “primer paciente vinculado”.

---

## 5. Definition of Done

- Ningún dato crítico de pacientes/vínculos solo en `localStorage` en entrega final.
- Soft delete **no borra** fila de `Patient` salvo política explícita de GDPR (fuera de alcance salvo que el curso lo exija).
- Todos los endpoints de otras HUs pueden filtrar por vínculos de esta tabla.

---

## 6. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Identificador duplicado entre terapeutas | Unique `(therapist_id, external_id)` o global según negocio |
| Última sesión desincronizada | Una sola función helper reutilizada por lista pacientes y HU-05 |
| Ficha usa mock gráfico | Separar “datos clínicos API” vs “gráficos mock” hasta integrar HU-04 |

---

## 7. Dependencias

- **HU-07:** auth token, CORS, paginación si la lista crece mucho.
- **HU-05:** fecha última sesión en lista (annotate).

**Esta HU es prerequisito fuerte de:** HU-01, HU-02, HU-03, HU-04, HU-05 (filtrado “mis pacientes”).

---

---

## 8. Implementación backend entregada (resumen)

### 8.1 Rutas y contrato

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/patients/` | Lista paginada de vínculos del terapeuta; `q`, `clinicalStatus`, `includeDeleted`; `lastSessionAt` vía subconsulta sobre `Session`. |
| GET | `/api/v1/patients/<pk>/` | Ficha: prioriza vínculo **activo**; si solo hay soft-deleted, devuelve el más reciente. |
| POST | `/api/v1/patients/link/` | Crea o reutiliza `Patient` (`associationId` → `external_id`); restaura soft delete del mismo par si aplica. **409** si otro terapeuta tiene vínculo activo al mismo paciente (mismo `Patient` por `external_id`). |
| PATCH | `/api/v1/therapist-patients/<link_id>/` | `primaryDiagnosis`, `clinicalStatus`. |
| POST | `/api/v1/therapist-patients/<link_id>/unlink/` | `deleted_at` = ahora. |
| POST | `/api/v1/therapist-patients/<link_id>/restore/` | Limpia `deleted_at`. |

**403** si el usuario no tiene perfil `Therapist`. **404** en ficha o mutaciones sobre `link_id` ajeno (misma convención que historial de sesiones).

### 8.2 Archivos nuevos o actualizados

| Archivo | Rol |
|---------|-----|
| `RehabWeb_API/services/patient_links.py` | Queryset base con `last_session_at` anotado. |
| `RehabWeb_API/filters.py` | `TherapistPatientListFilter` (`q`, `clinicalStatus`, `includeDeleted`). |
| `RehabWeb_API/serializers.py` | `TherapistPatientRowSerializer`, `PatientLinkRequestSerializer`, `TherapistPatientPatchSerializer`. |
| `RehabWeb_API/views/patient_management.py` | Vistas HU-06; paginación `APIPageNumberPagination`. |
| `RehabWeb_API/api_urls.py` | Rutas `patients/`, `patients/link/`, `patients/<pk>/`, `therapist-patients/...`. |
| `RehabWeb_API/views/__init__.py` | Export de vistas pacientes. |
| `RehabWeb_API/tests/test_patients_api.py` | Auth, flujo link→patch→unlink→restore, 409, 404 ficha. |
| `RehabWeb_API/documentacion/modulo5/Contrato-API-endpoints-DTO-serializers.md` | Nombres de serializers HU-06. |
| `README.md` | Sección HU-06 y árbol (`patient_management.py`). |

### 8.3 Qué deben hacer los compañeros

1. `makemigrations` / `migrate` si aún no aplicaron modelos de paciente/vínculo.
2. Sembrar pacientes de prueba; validar lista y ficha con token.
3. Integrar Angular: `PatientsRegistryService` → estos endpoints; eliminar dependencia de `localStorage` para datos de negocio.
4. `python manage.py test RehabWeb_API.tests` en local.

### 8.4 Fases del plan — estado

- Fases 2–3 y documentación: cubiertas en código + **§9** (contrato HTTP).
- Fase 4: tests de flujo y conflictos; ampliar en CI con MySQL si hace falta.
- Fases 1, 5–6: pendientes del equipo (migraciones ya generadas localmente, front, seeds).

---

## 9. Apéndice técnico — pacientes y vínculos

Convenciones: token DRF; JSON camelCase; **403** sin terapeuta; **404** en ficha o `therapist-patients/<linkId>/` ajeno.

### `GET /api/v1/patients/`

Vínculos del terapeuta con `lastSessionAt` (última `Session` del par). Paginación: `page`, `page_size` (máx. 50).

| Query | Descripción |
|-------|-------------|
| `q` | Nombre, `external_id`, `primary_diagnosis` (`icontains`). |
| `clinicalStatus` | `riesgo`, `activo`, `alta`. |
| `includeDeleted` | `true` incluye soft-deleted. |

Fila `results[]`: `patientId`, `linkId`, `associationId`, `fullName`, `primaryDiagnosis`, `clinicalStatus`, `lastSessionAt`, `deletedAt`, `isUnlinked`.

### `GET /api/v1/patients/<id>/`

`<id>` = PK de `Patient`; prioriza vínculo activo, si no el soft-delete más reciente.

### `POST /api/v1/patients/link/`

`fullName` obligatorio; `associationId` opcional; **409** si otro terapeuta tiene vínculo activo al mismo `Patient` (por `external_id`). 200/201 según actualización, restauración o alta.

### `PATCH /api/v1/therapist-patients/<linkId>/`

`primaryDiagnosis`, `clinicalStatus`.

### `POST .../unlink/` y `.../restore/`

Soft delete / reactivación; **400** si estado inconsistente.

### Orden de rutas en `api_urls.py`

Declarar `patients/link/` y `patients/<id>/performance-series/` antes de `patients/<pk>/` genérico.

---

*Última revisión del plan: 2026-04-23 (secciones 8–9).*
