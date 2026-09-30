# Documento de Requerimientos — Ontology Engine Framework (Migración a Estándares)

## Introducción

Este documento define los requerimientos para **migrar el esquema [IA] existente** de la base de datos `sqldb_buklo_lab` al cumplimiento 100% de los estándares de buklo_lab, y agregar las capas de backend (Gateway), orquestación IA (AI Core) y frontend (Angular).

**Estado actual:** El esquema `[IA]` ya tiene ~60 tablas, ~96 stored procedures (pa_con/pa_man) y ~12 sp_* de proceso. Las tablas de ontología ya existen con datos, pero fueron creadas con UNIQUEIDENTIFIER como PK, CHECK constraints inline, sin id_cat_company, y con campos created_at/updated_at (no estándar).

**Objetivo:** Migrar las tablas existentes a cumplir los estándares sin perder datos, actualizar SPs existentes con boilerplate obligatorio, y construir las capas 2-4 sobre esta base corregida.

### Estándares Obligatorios a Aplicar

- PKs `BIGINT IDENTITY(1,1)` — agregar columna BIGINT, migrar FKs, deprecar UNIQUEIDENTIFIER
- Multi-tenancy `id_cat_company` — agregar a toda tabla existente que no lo tenga
- Estados via `utility.cat_status` — reemplazar CHECK constraints inline
- Catálogos via `utility.cat_catalog` — reemplazar enumeraciones inline
- Auditoría: renombrar `created_at`→`create_date`, `created_by`→`create_user`, `updated_at`→`update_date`, `updated_by`→`update_user`
- Booleanos: ya usan SMALLINT ✅ (esto se cumple)
- SPs: agregar boilerplate (utility.pa_man_execution, TRY/CATCH, utility.pa_man_exception)
- Registro REST via `utility.pa_man_microservice_method`

### Inventario de Objetos Existentes a Migrar

**Tablas de ontología en [IA]:**
- ontology, ontology_entity_type, ontology_entity, ontology_entity_attribute, ontology_entity_attribute_enum, ontology_entity_tag, ontology_audit_log
- data_source, data_source_mapping, data_source_access_rule, data_source_agent_relation, data_source_process_relation
- causal_relationship, causal_relationship_context
- agent, agent_role, agent_dependency, agent_focus_area, agent_integration, agent_use_case, agent_preferred_index, agent_excluded_company, agent_decision_snapshot
- conversation_session, conversation_session_step, conversation_session_context
- artifact_reference
- operational_metric, operational_process, resource, metric_resource_impact, process_metric_relation, process_resource_relation, process_critical_stage, resource_saturation_relation
- golden_dataset + 5 tablas hijas
- analytical_task + 10 tablas hijas
- conflict_resolution_protocol, conflict_resolution_history
- tra_agent_conversations, tra_agent_messages, tra_agent_conversation_metrics
- analysis_event

**SPs existentes (~96):** pa_con_* y pa_man_* para cada tabla + sp_ontology_* (publish, archive, fork, validate, export, import, diff, prompt_context_build)

## Glosario

- **Migration_Script**: Script SQL que modifica tablas existentes (ALTER TABLE) para cumplir estándares sin perder datos.
- **PK_Migration**: El proceso de agregar columna `id_new BIGINT IDENTITY` a tablas con UNIQUEIDENTIFIER PK, actualizar FKs, y eventualmente hacer swap del PK.
- **Company_Backfill**: El proceso de agregar `id_cat_company` a tablas que no lo tienen y asignar un valor default para datos existentes.
- **Audit_Rename**: Renombrar columnas de auditoría: created_at→create_date, created_by→create_user, updated_at→update_date, updated_by→update_user.
- **Status_Migration**: Reemplazar CHECK constraints en columna status (VARCHAR) con FK a utility.cat_status.
- **Catalog_Migration**: Reemplazar CHECK constraints en columnas de tipo (VARCHAR) con FK a utility.cat_catalog.
- Los demás términos (Ontology_Engine, AI_Core, Trust_Boundary, Tool_Registry, etc.) mantienen la misma definición del spec anterior.

## Requerimientos

### Requerimiento 1: Migración de PKs — UNIQUEIDENTIFIER a BIGINT IDENTITY

**User Story:** Como DBA, quiero que todas las tablas del esquema [IA] tengan PKs BIGINT IDENTITY(1,1) para cumplir el estándar, manteniendo compatibilidad con datos existentes durante la transición.

#### Criterios de Aceptación

1. FOR ALL tablas en [IA] con PK UNIQUEIDENTIFIER, THE Migration SHALL agregar columna `id_new BIGINT IDENTITY(1,1) NOT NULL` como nueva PK.
2. THE Migration SHALL mantener la columna UNIQUEIDENTIFIER existente renombrada como `legacy_uuid` (UNIQUEIDENTIFIER NOT NULL) con índice UNIQUE para compatibilidad durante transición.
3. THE Migration SHALL actualizar todas las FKs que referencian la tabla migrada para apuntar a la nueva columna BIGINT.
4. THE Migration SHALL ejecutarse en un script idempotente que pueda re-ejecutarse sin error (IF NOT EXISTS antes de ALTER).
5. THE Migration SHALL preservar todos los datos existentes sin pérdida.
6. THE Migration SHALL agregar columna `identifier` (NVARCHAR(100)) en tablas que necesiten referencia portable para export/import (ontology, ontology_entity, data_source, etc.), poblada inicialmente con el valor de legacy_uuid convertido a string.

### Requerimiento 2: Agregar id_cat_company (Multi-Tenancy)

**User Story:** Como arquitecto, quiero que toda tabla en [IA] tenga `id_cat_company` para aislar datos por empresa siguiendo el patrón estándar.

#### Criterios de Aceptación

1. FOR ALL tablas en [IA] que no tengan `id_cat_company`, THE Migration SHALL agregar `id_cat_company BIGINT NOT NULL` con FK a `utility.cat_company`.
2. THE Migration SHALL asignar un valor default a `id_cat_company` para datos existentes (la company id de Grupo Montecristo, identificada previamente).
3. THE Migration SHALL agregar `id_cat_company` en los índices de uso frecuente para filtrado por empresa.
4. ALL SPs existentes SHALL ser actualizados para incluir `@p_id_cat_company` como parámetro y filtro obligatorio en consultas.

### Requerimiento 3: Migración de Campos de Auditoría

**User Story:** Como DBA, quiero que las columnas de auditoría sigan la convención estándar para consistencia con el resto de buklo_lab.

#### Criterios de Aceptación

1. FOR ALL tablas en [IA], THE Migration SHALL renombrar: `created_at` → `create_date`, `created_by` → `create_user`, `updated_at` → `update_date`, `updated_by` → `update_user`.
2. THE Migration SHALL cambiar el tipo de `create_date` y `update_date` de DATETIME2(7) a DATETIME (consistente con el resto del ecosistema).
3. THE Migration SHALL hacer `create_user` NOT NULL (con valor default 'SYSTEM' para datos existentes que tengan NULL).
4. ALL SPs existentes SHALL ser actualizados para usar los nuevos nombres de columnas.

### Requerimiento 4: Migración de Estados a utility.cat_status

**User Story:** Como arquitecto, quiero que los estados se gestionen via utility.cat_status en vez de CHECK constraints inline.

#### Criterios de Aceptación

1. THE Migration SHALL crear entradas en `utility.cat_meta_type` (key_00='buklo_lab', key_01='IA') para cada grupo de estados del módulo.
2. THE Migration SHALL crear registros en `utility.cat_status` para: ontology_version_status (draft, active, archived), conversation_session_status (active, completed, archived), artifact_status (active, superseded).
3. FOR ALL tablas con columna `status` VARCHAR + CHECK, THE Migration SHALL agregar columna `id_cat_status BIGINT FK a utility.cat_status`, poblar con los IDs correctos basado en el valor VARCHAR existente, y deprecar la columna VARCHAR original.
4. THE Migration SHALL actualizar los sp_ontology_* (publish, archive, fork) para buscar estados en utility.cat_status via cat_meta_type.

### Requerimiento 5: Migración de Clasificadores a utility.cat_catalog

**User Story:** Como arquitecto, quiero que los clasificadores (tipos, operadores, niveles) se gestionen via utility.cat_catalog.

#### Criterios de Aceptación

1. THE Migration SHALL crear entradas en `utility.cat_meta_type` para cada grupo de catálogo: ontology_source_type, ontology_mapping_type, ontology_access_level, ontology_value_type, ontology_operator, ontology_sensitivity, ontology_session_type, ontology_agent_type, ontology_agent_role, ontology_dependency_type.
2. THE Migration SHALL crear registros en `utility.cat_catalog` para cada valor de cada grupo.
3. FOR ALL tablas con columnas tipo VARCHAR + CHECK IN(...), THE Migration SHALL agregar columna `id_cat_catalog_[tipo] BIGINT FK`, poblar basado en el valor VARCHAR, y deprecar la columna CHECK.
4. Tablas afectadas: ontology_entity_attribute (type→id_cat_catalog_value_type), data_source (source_type→id_cat_catalog_source_type), data_source_mapping (mapping_type→id_cat_catalog_mapping_type), data_source_access_rule (access_type→id_cat_catalog_access_level), causal_relationship_context (operator), agent (mode→id_cat_catalog_agent_type).

### Requerimiento 6: Actualización de SPs con Boilerplate Estándar

**User Story:** Como desarrollador, quiero que todos los SPs existentes en [IA] incluyan el boilerplate obligatorio para trazabilidad de ejecución.

#### Criterios de Aceptación

1. ALL pa_con_* y pa_man_* existentes SHALL ser actualizados con CREATE OR ALTER para agregar: parámetros estándar (@p_user, @p_execution_mode, @p_option, @p_identifier_external), EXEC utility.pa_man_execution al inicio (consecutive=1) y al final (consecutive=99999), TRY/CATCH con utility.pa_man_exception.
2. ALL pa_man_* existentes SHALL insertar en [IA].[ontology_audit_log] antes de UPDATE/DELETE (auditoría de negocio dentro del SP, no triggers).
3. ALL sp_ontology_* (publish, archive, fork, validate, export, import, diff, prompt_context_build) SHALL ser actualizados con el mismo boilerplate.
4. THE Migration SHALL mantener compatibilidad con los parámetros de negocio existentes (los nuevos parámetros estándar se agregan, no se eliminan los existentes).

### Requerimiento 7: Tablas Nuevas (no existentes) — Siguiendo Estándares desde Inicio

**User Story:** Como arquitecto, quiero crear las tablas adicionales que el framework necesita y que aún no existen, directamente con estándares.

#### Criterios de Aceptación

1. THE Ontology_Engine SHALL crear `[IA].[cat_relationship_type]` (BIGINT PK, id_cat_company, slug, name, label, is_causal SMALLINT, is_directional SMALLINT, inverse_slug, source_entity_types JSON, target_entity_types JSON, auditoría estándar) — para formalizar tipos de relación que actualmente están en el campo `type` de causal_relationship.
2. THE Ontology_Engine SHALL crear `[IA].[cat_agent_tool]` (BIGINT PK, id_cat_company, slug, name, description, parameters_schema JSON, implementation_type, implementation_config JSON, auditoría estándar) — para herramientas custom por company.
3. IF otras tablas son necesarias para el AI Core (e.g., tablas de sesiones extendidas), SHALL crearse directamente con estándares (BIGINT PK, id_cat_company, campos auditoría estándar, FKs a cat_status/cat_catalog).

### Requerimiento 8: Seeds del Módulo (cat_meta_type + cat_status + cat_catalog)

**User Story:** Como DBA, quiero seeds idempotentes que registren los estados y catálogos del módulo.

#### Criterios de Aceptación

1. THE Migration SHALL crear seeds idempotentes (DELETE key_## + INSERT) para 13+ entradas cat_meta_type con key_00='buklo_lab', key_01='IA'.
2. THE Migration SHALL crear seeds para cat_status (version: draft/active/archived, session: active/completed/archived, artifact: active/superseded).
3. THE Migration SHALL crear seeds para cat_catalog (source_type, mapping_type, access_level, value_type, operator, sensitivity, session_type, agent_type, agent_role, dependency_type con todos sus valores).
4. Seeds SHALL seguir el patrón estándar de scripts: SET NOCOUNT ON, TRY/CATCH, TRANSACTION, SELECT de validación final.

### Requerimiento 9: Registro REST de SPs

**User Story:** Como desarrollador frontend, quiero que los SPs estén registrados en restful.tra_method para ser invocables desde el Gateway.

#### Criterios de Aceptación

1. THE Migration SHALL registrar todos los SPs de [IA] (pa_con_*, pa_man_*, sp_*) como métodos en restful.tra_method via utility.pa_man_microservice_method.
2. SHALL usar search_key `method:get:{sp_name}` para pa_con_*, `method:post:{sp_name}` para pa_man_* y sp_*.
3. SHALL usar config: microservice:engine, provider:ssql, DEV.CRM, sql:buklo_lab, execute.
4. SHALL usar @p_json_column_definitions para SPs que reciben parámetros JSON.
5. Rutas de chat (AI Core) SHALL registrarse como Tipo B (provider:microservice, route custom).

### Requerimiento 10: Pantallas CRUD Buklo

**User Story:** Como administrador, quiero pantallas de administración para gestionar ontología.

#### Criterios de Aceptación

1. THE Ontology_Engine SHALL proveer configs buklo CRUD para: ontology (versiones), entity_type, entity (con attrs/tags), causal_relationship, data_source (con mappings), agents, audit_log.
2. SHALL agregar acciones de "Publicar", "Archivar", "Fork", "Validar" en pantalla de ontology.
3. Cada config SHALL apuntar al pa_con/pa_man correspondiente ya existente (ahora con boilerplate estándar).

### Requerimiento 11: Refactorización de Servicios MAA (Frontend)

**User Story:** Como desarrollador frontend, quiero que los servicios consuman APIs del backend en lugar de JSON estáticos.

#### Criterios de Aceptación

1. OntologyService SHALL cargar desde endpoint Gateway (sp_ontology_prompt_context_build) con fallback a JSON estático.
2. ArtifactStoreService SHALL persistir via Gateway (pa_man_artifact_reference) con fallback a localStorage.
3. GoldenDatasetService SHALL cargar desde Gateway con fallback.
4. SHALL mantener interfaces públicas existentes.

### Requerimiento 12: Serialización/Deserialización (Export/Import)

**User Story:** Como ingeniero, quiero exportar/importar ontologías por slug/identifier (no por BIGINT IDs).

#### Criterios de Aceptación

1. sp_ontology_export SHALL ser actualizado para serializar usando identifier/slug como referencia portable.
2. sp_ontology_import SHALL ser actualizado para resolver relaciones por identifier/slug matching y generar nuevos BIGINT IDs.
3. Propiedad round-trip: export → import produce versión equivalente en contenido.

### Requerimiento 13: Rich Messages, Snapshot, Diff, Version Diff View

**User Story:** Como usuario, quiero funcionalidades de chat enriquecido, snapshots inmutables y diff visual.

#### Criterios de Aceptación

1. THE Ontology_Engine SHALL definir sistema de Rich_Message (12 tipos), interfaces TypeScript compartidas, ChatAction extendido.
2. Snapshot: al crear sesión, registrar el id de la ontología activa en conversation_session para inmutabilidad.
3. sp_ontology_diff (ya existe) SHALL exponerse via Gateway y tener componente frontend visual.

### Requerimiento 14: Microservicio AI Core

**User Story:** Como arquitecto, quiero un microservicio de orquestación de agentes IA (TCP 3004) sin frameworks externos.

#### Criterios de Aceptación

1. AI Core: NestJS, TCP 3004, Intent Classifier, Agent Executor Loop (max 10 iteraciones), Trust Boundary, LLM Provider Adapter (OpenAI, Anthropic, Ollama), Tool Registry, SSE streaming.
2. Comunicación con Engine Core via TCP 3001 para ejecutar SPs (query data, persist artifacts).
3. Auth service-to-service con JWT interno.
4. Cache de contexto de ontología en Redis (TTL 10min).
5. Sin dependencias de frameworks de orquestación (solo SDKs de LLM providers).

### Requerimiento 15: SSE Streaming y Rutas de Chat en Gateway

**User Story:** Como usuario, quiero respuestas en tiempo real token-por-token.

#### Criterios de Aceptación

1. Gateway: POST /api/chat/message → TCP a AI Core. GET /api/chat/stream/:sessionId → proxy SSE.
2. Eventos SSE: token, tool_start, tool_end, rich_message, error, done.
3. Reconexión con Last-Event-ID (buffer Redis TTL 5min).
4. Rate limiting: 20 msg/min, 5 sesiones SSE concurrentes por usuario.
5. Timeout configurable (default 120s).
