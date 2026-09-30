# Implementation Plan: Ontology Engine Framework (Migración a Estándares)

## Overview

Migración del esquema `[IA]` existente (~60 tablas, ~96 SPs) a cumplimiento 100% estándares buklo_lab, más construcción de capas Gateway, AI Core y Frontend. Estrategia: ALTER TABLE in-place, no esquema nuevo.

## Tasks

---

## FASE 0: Preparación — Seeds de cat_meta_type, cat_status, cat_catalog

- [x] 1. Crear seeds de cat_meta_type para el módulo [IA]
  - [x] 1.1 Script `0100_seed_cat_meta_type_ontology.sql` — 13 entradas (key_00='buklo_lab', key_01='IA'): ontology_version_status, ontology_session_status, ontology_artifact_status, ontology_source_type, ontology_mapping_type, ontology_access_level, ontology_value_type, ontology_operator, ontology_sensitivity, ontology_session_type, ontology_agent_type, ontology_agent_role, ontology_dependency_type. Patrón: DELETE key_## + INSERT.
    - _Requerimientos: 8.1_
  - [x] 1.2 Script `0110_seed_cat_status_ontology.sql` — Estados: version (draft, active, archived), session (active, completed, archived), artifact (active, superseded). FK a cat_meta_type creados en 1.1.
    - _Requerimientos: 8.2_
  - [x] 1.3 Script `0120_seed_cat_catalog_ontology.sql` — Catálogos: source_type(4), mapping_type(4), access_level(5), value_type(5+), operator(8), sensitivity(4), session_type(3), agent_type(6), agent_role(4), dependency_type(2). FK a cat_meta_type.
    - _Requerimientos: 8.3_

- [x] 2. Checkpoint — Verificar seeds ejecutan sin error, SELECT validación muestra registros correctos

---

## FASE 1: Migración DDL — ALTER TABLE en tablas existentes

- [x] 3. Migración de campos de auditoría (RENAME)
  - [x] 3.1 Script `0011_alter_rename_audit_columns.sql` — Para TODAS las tablas en [IA]: EXEC sp_rename created_at→create_date, created_by→create_user, updated_at→update_date, updated_by→update_user. Cambiar tipo DATETIME2(7)→DATETIME. Hacer create_user NOT NULL con DEFAULT 'SYSTEM' para NULLs existentes.
    - _Requerimientos: 3.1-3.4_

- [ ] 4. Agregar id_cat_company a todas las tablas
  - [~] 4.1 Script `0012_alter_add_id_cat_company.sql` — ADD id_cat_company BIGINT NOT NULL con DEFAULT=[id_company_montecristo] para todas las tablas que no lo tengan. ADD FK a utility.cat_company.
    - _Requerimientos: 2.1-2.3_

- [ ] 5. Agregar columnas de estado y catálogo (FK a cat_status/cat_catalog)
  - [~] 5.1 Script `0013_alter_add_status_fks.sql` — ADD id_cat_status BIGINT a: ontology, conversation_session, artifact_reference. UPDATE poblando basado en valor VARCHAR existente. 
    - _Requerimientos: 4.1-4.3_
  - [~] 5.2 Script `0014_alter_add_catalog_fks.sql` — ADD id_cat_catalog_* BIGINT a: ontology_entity_attribute (type), data_source (source_type, sensitivity), data_source_mapping (mapping_type), data_source_access_rule (access_type), causal_relationship_context (operator), agent (mode→agent_type), conversation_session (session_type), agent_role (role). UPDATE poblando basado en VARCHAR existente.
    - _Requerimientos: 5.1-5.4_

- [ ] 6. Migración de PKs — UNIQUEIDENTIFIER a BIGINT IDENTITY
  - [~] 6.1 Script `0015_alter_pk_migration_parents.sql` — Para tablas padre (ontology, agent, data_source): ADD id_new BIGINT IDENTITY, RENAME id→legacy_uuid, RENAME id_new→id, DROP/CREATE PK, ADD UNIQUE INDEX en legacy_uuid, ADD identifier NVARCHAR(100).
    - _Requerimientos: 1.1-1.6_
  - [~] 6.2 Script `0016_alter_pk_migration_children.sql` — Para tablas hijas: ADD nuevas FK BIGINT, populate via JOIN a padre.legacy_uuid, DROP FK vieja, ADD nueva FK constraint.
    - _Requerimientos: 1.3_
  - [~] 6.3 Script `0017_alter_pk_migration_grandchildren.sql` — Para tablas nietas (entity_attribute, entity_tag, relationship_condition, data_source_mapping, etc.): mismo patrón.
    - _Requerimientos: 1.3_

- [ ] 7. Crear tablas nuevas (no existentes)
  - [~] 7.1 Script `0018_create_cat_relationship_type.sql` — [IA].[cat_relationship_type] con BIGINT PK, id_cat_company, slug, name, label, is_causal SMALLINT, is_directional SMALLINT, inverse_slug, source_entity_types JSON, target_entity_types JSON, auditoría estándar.
    - _Requerimientos: 7.1_
  - [~] 7.2 Script `0019_create_cat_agent_tool.sql` — [IA].[cat_agent_tool] con BIGINT PK, id_cat_company, slug, name, description, parameters_schema JSON, implementation_type, implementation_config JSON, auditoría estándar.
    - _Requerimientos: 7.2_

- [~] 8. Checkpoint — Verificar migración DDL completa: contar registros (debe ser igual a pre-migración), verificar FKs, verificar id_cat_company poblado, verificar id_cat_status/cat_catalog poblados

---

## FASE 2: Actualización de Stored Procedures

- [ ] 9. Actualizar SPs de ontología core con boilerplate
  - [~] 9.1 CREATE OR ALTER pa_con_ontology — agregar @p_user, @p_execution_mode, @p_option, @p_identifier_external, @p_id_cat_company, utility.pa_man_execution, TRY/CATCH, filtro por id_cat_company, usar id_cat_status en vez de status VARCHAR
    - _Requerimientos: 6.1-6.4_
  - [~] 9.2 CREATE OR ALTER pa_man_ontology — mismo boilerplate + insertar en ontology_audit_log antes de UPDATE/DELETE
    - _Requerimientos: 6.1-6.4_
  - [~] 9.3 Actualizar pa_con/pa_man para: ontology_entity_type, ontology_entity (con attrs/tags), data_source (con mappings), data_source_access_rule, causal_relationship
    - _Requerimientos: 6.1-6.4_

- [ ] 10. Actualizar SPs de agentes y sesiones
  - [~] 10.1 Actualizar pa_con_agent, pa_man_agent (y tablas hijas: agent_role, agent_dependency, agent_integration, etc.) con boilerplate + id_cat_company
    - _Requerimientos: 6.1-6.4_
  - [~] 10.2 Actualizar pa_con_conversation_session, pa_man_conversation_session (y tablas hijas) con boilerplate + id_cat_company + id_cat_status
    - _Requerimientos: 6.1-6.4_
  - [~] 10.3 Actualizar pa_con_artifact_reference, pa_man_artifact_reference
    - _Requerimientos: 6.1-6.4_

- [ ] 11. Actualizar SPs de proceso (sp_ontology_*)
  - [~] 11.1 CREATE OR ALTER sp_ontology_publish — agregar boilerplate, buscar estados en cat_status via cat_meta_type (no hardcoded 'active'/'draft')
    - _Requerimientos: 6.3, 4.4_
  - [~] 11.2 CREATE OR ALTER sp_ontology_archive — mismo patrón
    - _Requerimientos: 6.3_
  - [~] 11.3 CREATE OR ALTER sp_ontology_fork — actualizar para usar BIGINT IDs, slug matching para copiar
    - _Requerimientos: 6.3_
  - [~] 11.4 CREATE OR ALTER sp_ontology_validate — actualizar para FKs BIGINT
    - _Requerimientos: 6.3_
  - [~] 11.5 CREATE OR ALTER sp_ontology_export — serializar por identifier/slug (no UUID)
    - _Requerimientos: 12.1_
  - [~] 11.6 CREATE OR ALTER sp_ontology_import — deserializar por slug matching, nuevos BIGINT IDs
    - _Requerimientos: 12.2_
  - [~] 11.7 CREATE OR ALTER sp_ontology_diff — actualizar para BIGINT
    - _Requerimientos: 6.3_
  - [~] 11.8 CREATE OR ALTER sp_ontology_prompt_context_build — agregar @p_id_cat_company, boilerplate
    - _Requerimientos: 6.3_

- [ ] 12. Actualizar SPs restantes (~60+ SPs de tablas auxiliares)
  - [~] 12.1 Actualizar en batch todos los pa_con/pa_man de: golden_dataset (5 tablas), operational_metric, operational_process, resource, process_* relations, task_* (10+ tablas), analysis_event, conflict_resolution, tra_agent_conversations
    - _Requerimientos: 6.1_

- [~] 13. Checkpoint — Ejecutar cada SP con parámetros de prueba, verificar utility.pa_man_execution registra, verificar auditoría en ontology_audit_log

---

## FASE 3: Registro REST y Backend

- [ ] 14. Registro REST de todos los SPs
  - [~] 14.1 Script `0300_register_ontology_methods.sql` — Registrar ~30 SPs principales (pa_con_ontology, pa_man_ontology, pa_con_agent, pa_man_agent, sp_ontology_publish, etc.) via utility.pa_man_microservice_method. search_key: method:get:sp_name / method:post:sp_name.
    - _Requerimientos: 9.1-9.4_
  - [~] 14.2 Script `0310_register_ontology_chat_methods.sql` — Registrar rutas de chat (Tipo B: provider:microservice): ai/chat/message (POST), ai/chat/stream/:sessionId (GET).
    - _Requerimientos: 9.5_

- [ ] 15. Agregar rutas de chat al Gateway Core
  - [~] 15.1 ChatGatewayController: POST /api/chat/message, GET /api/chat/stream/:sessionId, JWT validation, rate limiting
    - _Requerimientos: 15.1-15.4_
  - [~] 15.2 Registrar AI Core en SERVICE_REGISTRY
    - _Requerimientos: 14.1_

---

## FASE 4: AI Core (Microservicio)

- [~] 16. Scaffold microservicio-ai-core (NestJS, TCP 3004)
    - _Requerimientos: 14.1_

- [~] 17. LLM Provider Adapter (OpenAI, Anthropic, Ollama + fallback)
    - _Requerimientos: 14.1_

- [~] 18. Tool Registry + 7 tools base (query_elasticsearch, query_sql, get_entity, get_related, calculate_metric, create_artifact, generate_chart)
    - _Requerimientos: 14.1_

- [~] 19. Trust Boundary + Intent Classifier + Agent Executor Loop (max 10 iteraciones)
    - _Requerimientos: 14.1_

- [~] 20. SSE Streaming + Session Management + Redis cache
    - _Requerimientos: 14.1, 15.1-15.5_

- [~] 21. Auth service-to-service (JWT interno) + Data Access Rules enforcement
    - _Requerimientos: 14.1_

---

## FASE 5: Frontend (Angular)

- [~] 22. Configs Buklo CRUD (7+ pares table-config/form-config) apuntando a SPs migrados
    - _Requerimientos: 10.1-10.3_

- [~] 23. Refactorizar servicios MAA (OntologyService, ArtifactStore, GoldenDataset) — Gateway con fallback
    - _Requerimientos: 11.1-11.4_

- [~] 24. Rich Messages (11 componentes), Chat SSE, Version Diff visual, rutas y navegación
    - _Requerimientos: 13.1-13.3_

- [~] 25. Agregar method keys al environment engine.ts
    - _Requerimientos: 9.1_

- [~] 26. Checkpoint final — Compilación limpia, CRUD funcional, chat conecta a AI Core

## Notes

- **MIGRACIÓN IN-PLACE**: No se crea esquema [ontology] nuevo. Se modifica [IA] directamente.
- **BACKUP OBLIGATORIO** antes de cada fase de migración DDL.
- **Orden de ejecución**: Seeds (Fase 0) → DDL (Fase 1) → SPs (Fase 2) → REST (Fase 3) → AI Core (Fase 4) → Frontend (Fase 5)
- Las Fases 0-3 se ejecutan en el proyecto `database/project_sqldb_buklo_lab`.
- Las Fases 4-5 se ejecutan en los proyectos `Backend` y `frontend-apps`.
- PKs BIGINT IDENTITY — columna legacy_uuid se mantiene como UNIQUE INDEX para compatibilidad.
- Todas las tablas tendrán id_cat_company después de migración — filtro obligatorio en todos los SPs.
- Export/Import por identifier/slug (no por BIGINT IDs que no son portables).
- SPs existentes se actualizan con CREATE OR ALTER — no se borran y recrean.
