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

- **Frontend:** `reports-page`, `ClinicalExportFiltersDto`, `TherapistSessionService`; descarga CSV demo; PDF sin binario. Pendiente: `HttpClient` + `responseType: 'blob'` contra este endpoint.
- **Backend:** implementado `POST /api/v1/reports/export/` (ver sección 8). **AuditLog** en modelo sigue siendo opcional recomendado; hoy se registra un `INFO` en log al exportar.

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

## 8. Implementación backend entregada (resumen)

### 8.1 Decisiones tomadas (Fase 0)

| Tema | Decisión |
|------|----------|
| PDF | **ReportLab** (Python puro; cómodo en Windows). |
| Excel | **openpyxl** (`.xlsx`). |
| Síncrono / asíncrono | **Síncrono** con `FileResponse` (sin cola `ExportJob` por ahora). |
| Auth | **Token DRF** + existencia de fila `Therapist`; vínculo activo con el `patientId`. |

### 8.2 Archivos nuevos o actualizados

| Archivo | Rol |
|---------|-----|
| `requirements.txt` | Dependencias `openpyxl`, `reportlab`. |
| `RehabWeb_API/services/therapist_access.py` | `get_therapist_for_user`, `get_active_therapist_patient_link` (reutilizable por otras HUs). |
| `RehabWeb_API/services/clinical_export.py` | Consulta de sesiones por rango, `build_pdf_bytes` / `build_xlsx_bytes`, `render_clinical_export`, constante `MAX_EXPORT_RANGE_DAYS` (366). |
| `RehabWeb_API/serializers.py` | `ClinicalExportRequestSerializer` (`patientId`, `dateFrom`, `dateTo`, `format`). |
| `RehabWeb_API/views/reports.py` | `ReportExportAPIView` → `POST` con adjunto. |
| `RehabWeb_API/api_urls.py` | Ruta `reports/export/`. |
| `RehabWeb_API/services/dashboard_metrics.py` | Usa `get_therapist_for_user` (refactor mínimo). |
| `RehabWeb_API/views/__init__.py` | Exporta `MeDashboardAPIView` y `ReportExportAPIView` (corrección del nombre del dashboard). |
| `RehabWeb_API/tests/test_clinical_export_serializers.py` | Validación de fechas y rango. |
| `RehabWeb_API/tests/test_clinical_export_build.py` | PDF/XLSX no vacíos sin ORM. |
| `RehabWeb_API/tests/test_clinical_export_api.py` | 401, 403 sin terapeuta, 200 con mocks. |
| `README.md` | Sección HU-02 + tabla de tecnologías (ver diff en repo). |

### 8.3 Qué deben hacer los compañeros

1. `pip install -r requirements.txt` (nuevas librerías).
2. `makemigrations` / `migrate` y datos: `Therapist`, vínculo activo con `Patient`, `Session` en el rango de prueba.
3. Probar con `curl` o Postman: `POST /api/v1/reports/export/` con JSON y cabecera `Authorization: Token …`.
4. Integrar el front: dejar de generar CSV en cliente; descargar **blob** y nombre desde `Content-Disposition`.
5. Opcional: modelo `AuditLog` y persistencia de exportaciones; cola asíncrona si los PDF grandes dan timeout.
6. Ejecutar en local: `python manage.py test RehabWeb_API.tests` (incluye pruebas nuevas).

### 8.4 Pendientes explícitos respecto al plan original

- **JWT (AC-03 de la historia):** el stack sigue en token DRF; migrar a JWT implica cambio transversal documentado en el contrato API.
- **AuditLog:** solo logging por ahora.
- **Ejercicios por sesión:** la plantilla exporta filas de `Session`; si el producto exige `SessionExercise`, ampliar query y tablas en el mismo servicio.

---

## 9. Apéndice técnico — `POST /api/v1/reports/export/`

### Autenticación

- Cabecera: `Authorization: Token <clave>` (token DRF; la HU menciona JWT — el stack actual usa token hasta que se migre).

### Cuerpo JSON (camelCase)

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `patientId` | int | Sí | ID del paciente en la tabla `Patient`. |
| `dateFrom` | string (fecha ISO) | Sí | Inicio del periodo (inclusive), p. ej. `2026-01-01`. |
| `dateTo` | string (fecha ISO) | Sí | Fin del periodo (inclusive). |
| `format` | string | Sí | `pdf` o `xlsx`. |

Validación en servidor: `dateFrom` ≤ `dateTo`; rango máximo **366 días** (`MAX_EXPORT_RANGE_DAYS` en `services/clinical_export.py`); usuario con perfil `Therapist` y vínculo **activo** con ese `patientId`.

### Respuesta exitosa (200)

- Cuerpo: **bytes** del archivo.
- `Content-Type`: `application/pdf` o `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`.
- `Content-Disposition`: `attachment; filename="informe_clinico_p{id}_{desde}_{hasta}.pdf"` (o `.xlsx`).

### Códigos de error habituales

| Código | Situación |
|--------|-----------|
| 400 | Cuerpo inválido (serializer). |
| 401 | Sin autenticación. |
| 403 | Sin perfil terapeuta o sin vínculo activo con el paciente. |
| 500 | Error al generar PDF/XLSX (ver logs del servidor). |

*Implementación: `RehabWeb_API/views/reports.py`, `RehabWeb_API/services/clinical_export.py`.*

---

*Última revisión del plan: 2026-04-23 (secciones 8–9).*
