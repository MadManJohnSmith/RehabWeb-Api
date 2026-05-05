# Reporte de trabajo — Frontend (Módulo 5)

Documento vivo: resume **qué se entregó en front** por historia de usuario (HU), en lenguaje claro y con detalle técnico cuando aporta contexto. Las historias nuevas se añaden **al final**, manteniendo el mismo formato.

**Referencias de producto:** `Historias de Usuario Modulo 5.md`, `Checklist-HU-Modulo-5-Frontend.md`, `Baseline-Tokens.md`.

---

## HU-01 — Dashboard de progreso visual

### Resumen (qué hace el usuario)

En el **tablero de control** (`/app`, ruta `dashboard`) el terapeuta ve un resumen con datos de demostración: alertas de inactividad, indicadores en anillo, **ROM semanal en barras**, una **gráfica de evolución** con línea de meta y línea observada, paneles laterales y tabla de sesiones recientes. Al pasar el ratón por los puntos de la gráfica aparece un texto con **valores numéricos** y el criterio de tendencia. Los puntos se pintan en **verde / coral / gris** según si respecto al **periodo anterior** hubo mejora, regresión o sin cambio (primer punto en gris).

### Detalle técnico

| Tema | Entrega |
|------|---------|
| Mock tipo API | `DashboardMetricsDto`, `DASHBOARD_METRICS_MOCK`, `DashboardDataService` (`getDashboardMetrics()`). El componente consume el payload con `toSignal`. |
| ROM | Sección dedicada alimentada por `romByWeek` del mismo mock. |
| N vs N−1 | Lógica en `dotsNvNMinus1` sobre `temporalSeries[].observedValue`. |
| Rendimiento (AC-03) | Datasets acotados; nota en UI y **§6** en `Baseline-Tokens.md` (sin Lighthouse en repo). |
| Rutas / vista | `DashboardPageComponent` — `src/app/workspace/pages/dashboard/`. |

### Ajustes de interfaz relacionados (misma época)

- **Barra lateral y contenido:** corrección de anchos flex y scroll para que el contenido no quede “despegado” y la **barra lateral no se desplace** con el scroll de la página (shell a altura de viewport, scroll solo en la columna principal).

---

## HU-02 — Generación de reportes clínicos

### Resumen (qué hace el usuario)

En **Generación de reportes** (`/app/reportes`) puede elegir **paciente** (obligatorio), **fecha desde** y **fecha hasta**; si algo falta o el rango es inválido, ve un aviso y los botones de exportación **no están activos**. **Descargar Excel** genera un **CSV de demostración** en el navegador y muestra un **toast**; **Descargar PDF** solo confirma el flujo con **toast** (no hay PDF binario). Hay un recuadro que muestra cómo iría la cabecera **`Authorization: Bearer …`** con un **token de terapeuta simulado** (no es login real).

### Detalle técnico

| Tema | Entrega |
|------|---------|
| Filtros + formulario | `ngModel` en paciente y fechas; `validateFilters()` / `isFormValid()`; botones `[disabled]` cuando el formulario es inválido. |
| Excel simulado | `Blob` + descarga `.csv` (solo en navegador; protegido con `isPlatformBrowser` por SSR). |
| PDF | Solo mensajes vía `ToastService` (sin backend). |
| JWT / rol terapeuta | `TherapistSessionService` + **§7** en `Baseline-Tokens.md`; DTO `ClinicalExportFiltersDto` para el cuerpo previsto de la petición. |
| Archivos | `reports-page.component.ts/html`, `therapist-session.service.ts`, `clinical-export-request.dto.ts`. |

---

## HU-03 — Alertas proactivas de inactividad

### Resumen (qué hace el usuario)

En el **tablero** (`/app`) el bloque **amarillo** de inactividad indica cuántos pacientes llevan **más de 3 días** sin sesión; cada tarjeta lleva al **perfil** de ese paciente. Hay un botón de texto **“Job en servidor”** con *tooltip* que explica que en producción un **Cron** revisaría esto cada día. En **Alertas de inactividad** (`/app/alertas`) hay una **tabla** con el mismo criterio, enlaces al perfil y nota al pie; otro control explica el Cron (solo copy en demo).

### Detalle técnico

| Tema | Entrega |
|------|---------|
| Regla > 3 días | Copy en banner y en página de alertas; mock con días 5, 6 y 7 (todos > 3). |
| Enlaces | Tarjetas del dashboard → `[routerLink]="['/app/pacientes', p.patientId]"`; tabla → nombre + botón **Perfil** + `patientId` en `InactivityPatientDto` / filas mock. |
| Mock tipo lista | `InactivityAlertRowDto`, `INACTIVITY_ALERTS_MOCK`, `InactivityAlertsDataService.getAlerts()`. |
| Cron (N/A front) | `title` / `aria-label` en dashboard y en `/app/alertas`; **§8** en `Baseline-Tokens.md`. |
| Archivos | `dashboard-metrics.dto/mock`, `dashboard-page`, `inactivity-alerts.dto/mock`, `inactivity-alerts-data.service.ts`, `inactivity-alerts-page`. |

---

## HU-04 — Comparativa de desempeño (individual y grupal)

### Resumen (qué hace el usuario)

En **`/app/comparativa`** (menú **Comparativa de desempeño**) puede ver primero la **fórmula de progreso** en texto (hasta tener la imagen oficial del documento de HU). La **vista individual** permite elegir un paciente y ver **meta inicial** (línea discontinua) y **desempeño real** con puntos, leyenda y tooltips. La **vista grupal** permite marcar **varios pacientes** y ver en **un solo gráfico** sus curvas de desempeño real semanal (como proxy del *recovery score* en la demo), con leyenda por color.

### Detalle técnico

| Tema | Entrega |
|------|---------|
| Datos compartidos | `patient-detail.mock.ts` (`PATIENT_DETAIL_MOCK`, `PATIENT_DETAIL_IDS`); perfil de paciente importa el mismo mock. |
| Página | `ComparisonPerformancePageComponent` en `pages/comparison/`; ruta `comparativa` en `workspace.routes.ts`. |
| Gráficos | SVG + `computed` para puntos/líneas; grupo con escala común `groupBounds`. |
| Fórmula | Bloque en UI + **§9** en `Baseline-Tokens.md`. |

---

## HU-05 — Historial técnico de sesiones

### Resumen (qué hace el usuario)

En **`/app/historial-sesiones`** ve una tabla **de la más reciente a la más antigua**, puede **buscar** por texto, **filtrar por paciente** y cambiar **cuántas filas por página** (5, 10 o 15) con botones de página. Al pulsar la **flecha** de una fila se abre un **panel lateral** con el detalle de esa sesión (notas, ejercicios, adherencia de demo); la información llega **por red simulada** sin recargar toda la página.

### Detalle técnico

| Tema | Entrega |
|------|---------|
| Mock lista | `session-history.dto.ts`, `sessions-list.mock.ts` (`satisfies` + orden explícito). |
| API simulada | `SessionHistoryApiService`: `searchSessions` (`timer`), `getSessionDetail` (`HttpClient` + `delay` + JSON en `public/mock/session-history.json`). |
| UI | `session-history-page.component.ts/html`: `toSignal` + `combineLatest` + `switchMap`, panel, `RouterLink` a ficha del paciente. |

---

## HU-06 — Gestión y asociación de pacientes (CRUD)

### Resumen (qué hace el usuario)

En **`/app/pacientes`** ve una **tabla** con ID, identificador de asociación, nombre (enlace a la **ficha**), diagnóstico, **estado** (riesgo / activo / alta con colores), última sesión y un menú **⋮**. Puede **buscar**, **vincular** un paciente nuevo (modal), **editar el diagnóstico** desde otro modal, **desvincular** (baja lógica: la fila se atenúa y marca “Desvinculado”) o **reactivar**. Los cambios se guardan en el **navegador** (`localStorage`); al abrir la ficha, el diagnóstico editado se refleja ahí cuando corresponde.

### Detalle técnico

| Tema | Entrega |
|------|---------|
| Registro | `PatientsRegistryService` — seed desde `PATIENT_DETAIL_MOCK`, `linkPatient`, `updateCondition`, `unlink` / `restore`. |
| UI | `patients-list-page` — modales, `FormsModule`, menú flotante, overlay cierre. |
| Perfil | `patient-detail-page` — `computed` fusiona `getDetailExtra` / fila del registro con mock gráfico. |
| Icono | `more-vertical` en `UiIconComponent` (Lucide). |

---

## HU-07 — Infraestructura de interfaz y navegación

### Resumen (qué hace el usuario)

El shell mantiene navegación consistente entre escritorio y móvil: **sidebar colapsable**, **drawer** con hamburguesa y accesos a módulos clave (incluye configuración placeholder y cerrar sesión). En rutas con carga simulada, como **`/app/historial-sesiones`**, se muestran estados explícitos de **carga**, **vacío** y **error** con opción de reintento, en vez de fallos silenciosos. Las pantallas no implementadas siguen en **“en construcción”** para no romper flujo.

### Detalle técnico

| Tema | Entrega |
|------|---------|
| Shell | `shell-layout` + `shell-sidebar`: drawer móvil, overlay y colapso en desktop con mismas rutas. |
| Responsive | Tablas con `overflow-x-auto`; gráficas con `viewBox` y contenedores fluidos (`min-w-0`). |
| Carga/error/vacío | `session-history-page`: `listVm` con `loading/error`, skeleton, bloque de error + reintento y estado vacío, además de panel de detalle con fallback. |
| En construcción | rutas placeholder (`under-construction-page`) para módulos pendientes. |

---

## HU-08 en adelante — _(pendiente)_

Mismo formato que HU-03.

---

*Última actualización de contenido: HU-01 a HU-07 cubiertas en este reporte.*
