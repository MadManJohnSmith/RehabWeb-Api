# Historias de usuario — Módulo 5

Documento de historias de usuario (HU) y criterios de aceptación (AC) para el módulo operativo de PhysioMetrics.

---

## HU-01: Dashboard de progreso visual

**Descripción:** El terapeuta requiere la visualización del progreso general de los pacientes mediante gráficas interactivas para la identificación de tendencias de recuperación.

### Criterios de aceptación

- **AC-01 (Datos):** Ejecución de consultas SQL a tablas de métricas y mapeo de objetos JSON para el renderizado de gráficas de rango de movimiento (ROM) y series temporales.

- **AC-02 (Interactividad):** Implementación de eventos *mouseover* para mostrar valores exactos. Los nodos de datos deben presentar codificación de color: verde para mejora y rojo para regresión, basados en la comparativa del registro \(N\) frente al registro \(N-1\).

- **AC-03 (Rendimiento):** El tiempo de carga y renderizado de los componentes visuales no debe superar el umbral de 3 segundos.

### Nota de implementación (backend HU-01)

El endpoint **`GET /api/v1/me/dashboard/`** está implementado en Django/DRF: agrega métricas (`MetricPoint`), sesiones recientes, resumen de inactividad (criterio alineado con HU-03) y tendencias N vs N−1 en JSON **camelCase**. Detalle de implementación, checklist del equipo y **esquema JSON** del response: **`doc-historias/HU-01-plan-accion.md`** (secciones 8 y 9).

---

## HU-02: Generación de reportes clínicos

**Descripción:** Exportación de datos de pacientes en formatos estándar para su integración en expedientes físicos o distribución interdepartamental.

### Criterios de aceptación

- **AC-01 (Formatos):** Procesamiento de un *join* de datos clínicos en la capa de *backend* para la generación de archivos binarios en formatos PDF y Excel.

- **AC-02 (Filtros):** Inclusión de parámetros de selección por ID de paciente y rango de fechas previo a la ejecución de la exportación.

- **AC-03 (Seguridad):** Validación de autorización mediante JSON Web Token (JWT) restringida exclusivamente al rol de terapeuta.

### Nota de implementación (backend HU-02)

El endpoint **`POST /api/v1/reports/export/`** genera archivos binarios **PDF** (ReportLab) y **Excel .xlsx** (openpyxl) a partir de `Session` y del vínculo `TherapistPatient`, con validación de fechas y tope de rango en servidor. Autenticación actual: **token DRF** y perfil `Therapist` (equivalente funcional al “solo terapeuta” de la HU). Contrato HTTP y descubrimientos: **`doc-historias/HU-02-plan-accion.md`** (secciones 8 y 9).

---

## HU-03: Alertas proactivas de inactividad

**Descripción:** Notificación automática ante el cese de actividad en el tratamiento de un paciente para el seguimiento administrativo.

### Criterios de aceptación

- **AC-01 (Lógica):** Ejecución de un proceso programado (*Cron Job*) con periodicidad diaria para validar si la diferencia entre la fecha actual y la última sesión registrada es **> 3 días**.

- **AC-02 (UI):** Despliegue de una alerta en el *dashboard* mediante un componente de banner amarillo con hipervínculo al perfil del paciente identificado como inactivo.

### Nota de implementación (backend HU-03)

- **`GET /api/v1/inactivity-alerts/`:** lista en vivo de pacientes inactivos (misma regla que el resumen del dashboard HU-01: más de 3 días sin sesión o sin sesiones; última sesión por par terapeuta–paciente).
- **Comando** `python manage.py refresh_inactivity_alerts` **:** materializa la tabla `InactivityAlert` para el job diario (cron / Programador de tareas).
- Documentación técnica y plan: **`doc-historias/HU-03-plan-accion.md`** (secciones 8 y 9).

---

## HU-04: Comparativa de desempeño (individual y grupal)

**Descripción:** Comparación del desempeño real frente a objetivos establecidos para el ajuste de planes de rehabilitación.

### Criterios de aceptación

- **AC-01 (Cálculo):** Superposición de capas de «Meta inicial» frente a «Desempeño real». El cálculo del progreso se rige por la fórmula indicada en la siguiente figura:

  <!-- Sustituir la ruta cuando el activo esté en el repositorio -->
  ![Fórmula de cálculo de progreso](./image-20260311-233530.png)

  *Nota:* Si la imagen aún no está en el proyecto, colócala junto a este documento con el nombre `image-20260311-233530.png` o actualiza la ruta anterior.

- **AC-02 (Multiusuario):** Capacidad de selección múltiple de pacientes para la visualización de *Recovery Scores* comparativos en una única interfaz gráfica.

### Nota de implementación (backend HU-04)

- **`GET /api/v1/patients/<id>/performance-series/`** — serie temporal (`MetricPoint` tipo `temporal`), resumen con `recoveryScorePercent` (fórmula **placeholder** documentada hasta tener la imagen oficial de la HU).
- **`POST /api/v1/performance/compare/`** — cuerpo `{ "patientIds": [ … ] }` (PK enteros); respuesta con lista por paciente y **`groupBounds`** para escala común.
- Contrato de endpoints, fórmula placeholder y plan: **`doc-historias/HU-04-plan-accion.md`** (secciones 8 y 9).

---

## HU-05: Historial técnico de sesiones

**Descripción:** Revisión detallada de sesiones históricas para el análisis de la evolución técnica del paciente.

### Criterios de aceptación

- **AC-01 (Optimización):** Listado ordenado de forma cronológica descendente. Implementación de consultas paginadas para la gestión eficiente de la memoria en el cliente y en el servidor.

- **AC-02 (UX):** Ejecución de peticiones asíncronas (AJAX / *HTTP Client*) al seleccionar una sesión para cargar el detalle sin requerir el refresco total del DOM.

### Nota de implementación (backend HU-05)

- **`GET /api/v1/sessions/`** — lista **paginada** (`count`, `next`, `previous`, `results`), orden **desc** por `occurred_at`; filtros `patientId`, `search`; `page_size` (p. ej. 5, 10, 15).
- **`GET /api/v1/sessions/<id>/`** — detalle con `notes` y **`exercises`** (modelo `SessionExercise`).
- Contrato de listado/detalle y plan: **`doc-historias/HU-05-plan-accion.md`** (secciones 8 y 9).

---

## HU-06: Gestión y asociación de pacientes (CRUD)

**Descripción:** Administración de la lista de pacientes activos para la organización del panel de control.

### Criterios de aceptación

- **AC-01 (Asociación):** Funcionalidad de búsqueda y vinculación de pacientes existentes mediante identificador único (relación uno a muchos entre terapeuta y paciente).

- **AC-02 (Edición / baja):** Edición del diagnóstico principal desde la vista de lista. Implementación de borrado lógico (*soft delete*) para la desvinculación de pacientes a través de un menú de acciones contextuales.

- **AC-03 (Estado):** Indicador visual del estado actual del paciente clasificado en: **Riesgo**, **Activo** o **Alta**.

### Backend (API)

- **`GET /api/v1/patients/`** — lista **paginada** de vínculos (`patientId`, `linkId`, `associationId`, `fullName`, `primaryDiagnosis`, `clinicalStatus`, `lastSessionAt`, `deletedAt`, `isUnlinked`); filtros `q`, `clinicalStatus`, `includeDeleted`.
- **`GET /api/v1/patients/<id>/`** — ficha (misma forma de fila que lista).
- **`POST /api/v1/patients/link/`** — cuerpo: `associationId` (opcional), `fullName`, `primaryDiagnosis`, `clinicalStatus`; **409** si el paciente (por `external_id`) ya está vinculado activamente a otro terapeuta.
- **`PATCH /api/v1/therapist-patients/<linkId>/`** — `primaryDiagnosis`, `clinicalStatus`.
- **`POST /api/v1/therapist-patients/<linkId>/unlink/`** y **`POST .../restore/`** — soft delete / reactivación.
- Contrato de API pacientes/vínculos y plan: **`doc-historias/HU-06-plan-accion.md`** (secciones 8 y 9). Nombres de serializers alineados con **`Contrato-API-endpoints-DTO-serializers.md`**.

---

## HU-07: Infraestructura de interfaz y navegación

**Descripción:** Provisión de una interfaz responsiva que permita la navegación sistemática por los módulos operativos.

### Criterios de aceptación

- **AC-01 (Sidebar):** Menú lateral colapsable con accesos directos a *dashboard*, pacientes, reportes, configuración y terminación de sesión.

- **AC-02 (Expansividad):** Adaptabilidad técnica de todos los componentes (tablas, gráficas y menús) a diferentes resoluciones de pantalla (*mobile friendly*).

- **AC-03 (Manejo de errores):** Implementación de estados de carga y manejo de excepciones en la UI. En caso de ausencia de datos o módulos en desarrollo, se debe mostrar un estado controlado en lugar de excepciones de consola.

### Backend (contrato estable)

- **`GET /api/v1/health/`** — comprobación de servicio y base de datos (`SELECT 1`); sin token.
- **`POST /api/v1/auth/login/`** — cuerpo `username` / `password` → `{"token": "..."}`.
- **`POST /api/v1/auth/logout/`** — con token válido → **204**; invalida el token en servidor.
- **CORS** para Angular en `localhost:4200`; orígenes extra vía `DJANGO_CORS_EXTRA_ORIGINS`.
- **Paginación DRF** global `APIPageNumberPagination` (`page`, `page_size` ≤ 50) en listados acordados.
- Variables de entorno: `.env.example` + carga con `python-dotenv`.
- Infra (health, auth, CORS, paginación, códigos HTTP) y plan: **`doc-historias/HU-07-plan-accion.md`** (secciones 8 y 9).

---

*Documento generado para alineación de producto y desarrollo — Módulo 5.*
