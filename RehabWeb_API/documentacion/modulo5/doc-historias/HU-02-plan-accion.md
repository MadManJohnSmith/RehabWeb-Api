# Plan de acción — HU-02: Generación de reportes clínicos

**Propietario sugerido:** Integrante 2  
**Referencias:** Historias HU-02 · Plan backend §Integrante 2 · Reporte front HU-02 · Contrato API (`POST /api/v1/reports/export/`)

---

## 1. Objetivo de negocio

Exportar **datos clínicos** del paciente en **PDF y Excel** con filtros obligatorios, para expediente físico o distribución interdepartamental (`/app/reportes`).

---

## 2. Criterios de aceptación → trazabilidad

| AC | Historias | Estado front (reporte) | Backend / alineación |
|----|-----------|-------------------------|----------------------|
| AC-01 | Join en backend; archivos binarios PDF y Excel | Excel simulado como **CSV** en navegador; PDF solo **toast** | Generación real: **PDF** + **XLSX** (o XLS); `Content-Type` y `Content-Disposition` correctos |
| AC-02 | Filtros: ID paciente + rango fechas | `ngModel` + `validateFilters()` / botones deshabilitados | Validar en serializer: paciente obligatorio, `date_from` ≤ `date_to`, límite máximo de rango días |
| AC-03 | JWT; solo rol terapeuta | UI muestra `Authorization: Bearer …` simulado | **Unificar auth:** token DRF o migración JWT; grupo/flag **terapeuta** + `IsAuthenticated`; paciente debe estar en `TherapistPatient` del usuario |

---

## 3. Estado actual

- **Frontend:** `reports-page`, `ClinicalExportFiltersDto`, `TherapistSessionService`; descarga CSV demo; PDF sin binario.
- **Backend:** Sin endpoint de exportación; posible `AuditLog` recomendado en plan.

---

## 4. Fases de trabajo

### Fase 0 — Decisiones (crítico)

- [ ] Elegir stack: **PDF** (WeasyPrint, ReportLab, wkhtmltopdf, etc.) y **Excel** (openpyxl, xlsxwriter).
- [ ] Decidir **síncrono** (`FileResponse`) vs **asíncrono** (`ExportJob` + polling) si PDF es pesado.
- [ ] Documentar cabecera real: `Authorization: Token <key>` (o JWT) y actualizar UI para no enseñar `Bearer` si no aplica.

### Fase 1 — Modelo y permisos

- [ ] Permiso custom: “usuario es terapeuta” + “`patient_id` pertenece a sus vínculos activos”.
- [ ] Query de export: join `Patient`, `TherapistPatient`, `Session`, notas/ejercicios según plantilla acordada con producto.
- [ ] (Opcional) Modelo `ExportJob` + estados si se elige cola.

### Fase 2 — API

- [ ] `POST /api/v1/reports/export/` con cuerpo alineado a `ClinicalExportFiltersDto` (camelCase): `patientId`, `dateFrom`, `dateTo`, `format`: `pdf` | `xlsx`.
- [ ] Respuestas: 400 validación; 403 paciente no autorizado; 401 sin auth; 200/201 con archivo o URL de job.
- [ ] Límite anti-abuso: tamaño máximo de rango, timeout del worker documentado.

### Fase 3 — Seguridad y auditoría

- [ ] No incluir datos de otros pacientes en plantillas por error de query.
- [ ] (Recomendado) Registrar exportación en `AuditLog`: usuario, paciente, rango, formato, timestamp.

### Fase 4 — Tests

- [ ] Tests: 403 con paciente ajeno; 400 fechas inválidas; 200 genera bytes no vacíos y mime esperado.
- [ ] Test manual: abrir archivo generado en Excel/Visor PDF.

### Fase 5 — Integración frontend

- [ ] Sustituir generación CSV local por `HttpClient.post` con `responseType: 'blob'`, manejo de nombre archivo desde `Content-Disposition`.
- [ ] Toasts de éxito/error alineados a códigos HTTP del backend.
- [ ] Quitar o corregir el recuadro demo de `Bearer` para reflejar auth real.

### Fase 6 — Documentación

- [ ] README: dependencias del sistema (p. ej. WeasyPrint y libs OS), ejemplo de petición.
- [ ] Actualizar contrato API con códigos de error y nombres de campos finales.

---

## 5. Definition of Done

- PDF y XLSX **binarios** generados en servidor con datos de MySQL.
- Filtros obligatorios validados en servidor (no solo en UI).
- Solo terapeutas autenticados con permiso sobre el paciente.
- Front descarga desde API sin fabricar CSV en cliente (salvo fallback acordado temporal).

---

## 6. Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| JWT vs Token | Decisión única documentada; middleware o interceptor Angular único |
| PDF en Windows / deps | Documentar instalación; CI opcional con job que omita PDF si no hay deps |
| Tamaño de respuesta | Límite de rango; paginación interna de tablas en Excel si aplica |

---

## 7. Dependencias

- **HU-07:** CORS, settings, límites `DATA_UPLOAD_MAX_*` si hay subidas.
- **HU-06:** vínculo terapeuta–paciente y lista de pacientes para el selector (datos reales en front).

---

*Última revisión del plan: 2026-04-23.*
