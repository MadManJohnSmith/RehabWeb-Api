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

- **Frontend:** `patients-list-page`, `patient-detail-page`, menú ⋮, `localStorage` vía `PatientsRegistryService`.
- **Backend:** Sin modelos persistidos de paciente/vínculo en el repo actual; esta HU **desbloquea** casi todo el módulo.

---

## 4. Fases de trabajo

### Fase 0 — Modelado relacional

- [ ] Decidir: `User` estándar + grupo **terapeuta** vs modelo `Therapist` 1:1 (plan sugiere perfil opcional).
- [ ] `Patient`: nombre, identificadores, datos mínimos legales/clínicos acordados con el curso.
- [ ] `TherapistPatient`: FKs, `primary_diagnosis`, `clinical_status`, `deleted_at`, `external_link_id` o campo equivalente al “identificador de asociación” de la UI.
- [ ] Índices: `(therapist_id, deleted_at)`, `(therapist_id, clinical_status)`, búsqueda por nombre/`external_id`.

### Fase 1 — Migraciones y admin

- [ ] `makemigrations` / `migrate` en `rehab_db`.
- [ ] (Opcional) Registro en Django Admin solo staff para soporte.

### Fase 2 — API lista y detalle

- [ ] `GET /api/v1/patients/` — queryset de vínculos del usuario; query `includeDeleted`, `clinicalStatus`, `q`.
- [ ] Respuesta alineada a columnas de tabla: id, identificador asociación, nombre, diagnóstico, estado, última sesión (subquery o annotate desde `Session` — coordinar con HU-05).
- [ ] `GET /api/v1/patients/{id}/` — detalle para ficha y rutas de comparativa.

### Fase 3 — Mutaciones

- [ ] `POST /api/v1/patients/link/` — idempotencia si el identificador ya existe (¿re-vincular otro terapeuta? — política explícita).
- [ ] `PATCH` diagnóstico y/o estado.
- [ ] `POST .../unlink/` y `.../restore/` con respuestas coherentes para que la UI actualice fila sin `localStorage`.

### Fase 4 — Tests

- [ ] Flujo: crear usuario terapeuta + token; link; listar; patch; unlink lista atenuada; restore.
- [ ] Intento de acceso a paciente ajeno → 403/404 según convención.

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

*Última revisión del plan: 2026-04-23.*
