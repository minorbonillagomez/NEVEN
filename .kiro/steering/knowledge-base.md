---
inclusion: auto
---

# Base de Conocimiento — Buklo / MediSmart

Cuando trabajas en este proyecto, esta es la fuente de verdad de todo el contexto.

## Ubicación de la knowledge base

```
.kiro/knowledge-base/
├── README.md                          → Índice general y estado de proyectos
├── 00-indice/MAPA-COMPLETO.md         → Inventario completo: objetos, specs, fases
├── 01-contexto-empresa/EMPRESA.md     → MediSmart, productos, países, principios
├── 02-salesforce-crm/
│   ├── ESTADO-ACTUAL.md               → Diagnóstico, deuda técnica, dependencias
│   ├── REINGENIERIA.md                → 7 dominios, nuevos objetos, plan de migración
│   ├── CATALOGO.md                    → SKUs, familias, LWC wizard 6 pasos
│   └── ENDPOINTS-API.md               → Todos los REST endpoints (existentes + nuevos)
├── 03-arquitectura-backend/BACKEND.md → Monorepo, servicios, paquetes, auth, seguridad
├── 04-productos-digitales/
│   └── PRODUCTOS-DIGITALES.md         → Inventario de specs digitales y estado
├── 05-especificaciones-tecnicas/
│   └── SPECS-RESUMEN.md               → Resumen de los 22 specs de Kiro
├── 06-analisis-mercado/
│   └── COMPARATIVO-PLATAFORMAS.md     → MediSmart vs Zuora/Chargebee/Recurly
└── 07-roadmap/ROADMAP-MAESTRO.md      → 5 fases + Track B + métricas de éxito
```

## Reglas críticas (no negociables)

### Salesforce
- **Ambiente:** SOLO `medismart--test.sandbox.my.salesforce.com` — nunca tocar producción
- **Cobros:** `CA_BatchCobrosRecurrentesMS` **nunca** se interrumpe — comportamiento intocable
- **Campos protegidos Account:** `frecuenciapago__c`, `formapago__c`, `fechaproximocobro__c`, `estado_del_cliente__c`, `tosend__c`, `toupdate__c`, `encobroactual__c` — no deprecar sin migración de cobros completa
- **LWC:** siempre retrieve antes de modificar: `node deploy-lwc.js --component=X --retrieve`
- **Apex:** siempre retrieve antes de modificar: `node deploy-apex.js --retrieve --file=X`
- **configurationsPlan** (con s): carpeta vacía que causa error en retrieve — no tocar

### Backend
- **Flujo obligatorio:** App → Gateway → Engine → SF Adapter → Salesforce
- **Zero hardcode de SF IDs** — se obtienen de SOQL o tabla SQL de configuración
- **Picklists de SF siempre** — no hardcodear en frontend; usar endpoint `subscriptions/catalog/picklists`
- **SOQL seguro:** validar IDs con `/^[a-zA-Z0-9]{15,18}$/` antes de interpolar
- **Sin `console.log`** en producción — usar `SecureLoggerService`
- **Branch:** siempre `development`, nunca crear ramas nuevas

### Arquitectura general
- **Strangler Fig:** los sistemas legacy coexisten con los nuevos hasta validación 100%
- **Catálogo:** un equipo centralizado de producto gestiona la configuración — no es autoservicio
- **Multi-país nativo:** `Pais__c` en todos los objetos relevantes de Salesforce

## Spec principal activo

`.kiro/specs/salesforce-crm-reingenieria-completa/`
- `requirements.md` — 20 requerimientos con EARS + correctness properties
- `design.md` — 7 dominios, modelos de datos, componentes Apex, scripts
- `tasks.md` — 41 tareas en 5 fases con JSON dependency graph

## Scripts de trabajo en Salesforce

Todos en `tools/buklo-tools-salesforce/`:

```bash
node query.js "SELECT ..."              # SOQL query
node execute-anonymous.js "apex..."    # Ejecutar Apex anónimo
node tooling-query.js "SELECT ..."     # Tooling API (metadata)
node deploy-apex.js --file=Clase       # Deploy Apex
node deploy-apex.js --retrieve --file=Clase  # Retrieve Apex
node deploy-lwc.js --component=X       # Deploy LWC
node deploy-lwc.js --component=X --retrieve  # Retrieve LWC
node run-tests.js                      # Ejecutar tests Apex (debe quedar 24/24 verde)
node describe-object.js NombreObjeto   # Ver campos de un objeto
```
