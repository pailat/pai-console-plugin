# Ontología de Conocimiento

> Generado por `tools/gen-references.ts` desde pai-portal `4ae9b884` (2026-10-07 Merge pull request #159 from pailat/fix/0.2.5/package-cycle), `packages/contracts/src/knowledge/ontology.ts`. No editar a mano: regenerar.

Un `knowledge_link` (o un link en `knowledge_create`) solo se acepta si el par source → target aparece aquí. Si no, el error es `ONTOLOGY`.

## toulmin

### `grounds` (fundamenta)

Grounds (Toulmin): el source es el dato o afirmación en el que se apoya el claim destino.

- de *todos menos* `module`, `screen`, `flow`, `data_model`, `entity`, `component`, `actor`, `glossary_term` → a *todos menos* `fact`, `reference`, `module`, `screen`, `flow`, `data_model`, `entity`, `component`, `actor`, `glossary_term`

### `warrant` (justifica)

Warrant (Toulmin): el source es la regla o principio que conecta los grounds con el claim destino.

- de `business_rule`, `constraint`, `objective`, `pattern`, `concept`, `decision`, `adr` → a *todos menos* `fact`, `reference`, `module`, `screen`, `flow`, `data_model`, `entity`, `component`, `actor`, `glossary_term`

### `supports` (respalda)

Backing (Toulmin): el source es evidencia positiva del claim destino.

- de *todos menos* `module`, `screen`, `flow`, `data_model`, `entity`, `component`, `actor`, `glossary_term` → a *todos menos* `fact`, `reference`, `module`, `screen`, `flow`, `data_model`, `entity`, `component`, `actor`, `glossary_term`

### `opposes` (se opone a)

Contra-backing (Toulmin): el source es evidencia contraria al claim destino.

- de *todos menos* `module`, `screen`, `flow`, `data_model`, `entity`, `component`, `actor`, `glossary_term` → a *todos menos* `fact`, `reference`, `module`, `screen`, `flow`, `data_model`, `entity`, `component`, `actor`, `glossary_term`

### `rebuttal` (refutaría)

Rebuttal (Toulmin): el source describe la condición que invalidaría el claim destino.

- de *todos menos* `module`, `screen`, `flow`, `data_model`, `entity`, `component`, `actor`, `glossary_term` → a *todos menos* `fact`, `reference`, `module`, `screen`, `flow`, `data_model`, `entity`, `component`, `actor`, `glossary_term`

### `alternative_to` (fue alternativa a) — mismo kind en ambos extremos

El source fue una opción considerada y no elegida frente al claim destino (mismo kind).

- de *todos menos* `fact`, `reference`, `module`, `screen`, `flow`, `data_model`, `entity`, `component`, `actor`, `glossary_term` → a *todos menos* `fact`, `reference`, `module`, `screen`, `flow`, `data_model`, `entity`, `component`, `actor`, `glossary_term`

## lifecycle

### `supersedes` (reemplaza a) — mismo kind en ambos extremos

El source reemplaza al destino (mismo kind); al activarse marca el destino como superseded.

- de *todos menos* `fact`, `reference`, `module`, `screen`, `flow`, `data_model`, `entity`, `component`, `actor`, `glossary_term` → a *todos menos* `fact`, `reference`, `module`, `screen`, `flow`, `data_model`, `entity`, `component`, `actor`, `glossary_term`

### `contradicts` (contradice a)

Dos claims incompatibles entre sí; señal de conflicto abierto.

- de *todos menos* `fact`, `reference`, `module`, `screen`, `flow`, `data_model`, `entity`, `component`, `actor`, `glossary_term` → a *todos menos* `fact`, `reference`, `module`, `screen`, `flow`, `data_model`, `entity`, `component`, `actor`, `glossary_term`

## structural

### `contains` (contiene)

Contención estructural: módulo → partes, modelo de datos → entidades, componente C4 → componente del nivel inmediatamente inferior, ADR → decisión, flujo → subflujo. Fija container_id del destino.

- de `module` → a `module`, `screen`, `flow`, `data_model`, `entity`, `component`
- de `data_model` → a `entity`
- de `component` → a `component`
- de `adr` → a `decision`
- de `flow` → a `flow`

### `depends_on` (depende de)

El source necesita al destino para funcionar.

- de `module`, `component`, `entity`, `screen`, `flow` → a `module`, `component`, `entity`
- de `task` → a `task`

### `uses` (usa)

Pantalla, flujo o componente que usa una entidad, un modelo de datos o un componente (en C4, properties.description y technology describen la relación).

- de `screen`, `flow`, `component` → a `entity`, `data_model`, `component`

### `implements` (implementa)

El source materializa una regla, decisión, ADR, objetivo, patrón o runbook.

- de `component`, `module`, `flow`, `screen`, `task` → a `business_rule`, `decision`, `adr`, `objective`, `pattern`, `runbook`

### `constrains` (restringe a)

Regla o restricción que limita al destino.

- de `business_rule`, `constraint` → a `module`, `screen`, `flow`, `data_model`, `entity`, `component`, `decision`, `adr`

### `affects` (impacta a)

Decisión, ADR, riesgo o tarea que impacta al destino.

- de `decision`, `adr`, `risk`, `task` → a *todos menos* `glossary_term`

### `contributes_to` (contribuye a)

El source sirve a un objetivo de negocio.

- de `decision`, `adr`, `business_rule`, `module`, `flow`, `screen`, `component`, `task` → a `objective`

### `mitigates` (mitiga)

El source reduce la probabilidad o el impacto de un riesgo.

- de `decision`, `adr`, `business_rule`, `module`, `component`, `task`, `runbook` → a `risk`

### `threatens` (amenaza)

Riesgo que amenaza un objetivo o una parte de la estructura.

- de `risk` → a `objective`, `module`, `screen`, `flow`, `data_model`, `entity`, `component`

### `performs` (ejecuta)

Actor que ejecuta un flujo, usa una pantalla o usa un elemento C4 (la persona del diagrama C4).

- de `actor` → a `flow`, `screen`, `component`

### `navigates_to` (navega a)

Navegación entre pantallas.

- de `screen` → a `screen`

### `relates_to` (se relaciona con) — mismo kind en ambos extremos

Relación ERD entre entidades; properties.cardinality, label e identifying.

- de `entity` → a `entity`

### `documents` (documenta a)

Referencia o nota que documenta al destino.

- de `reference`, `note` → a *todos*

### `refers_to` (menciona)

Cualquier nodo que usa un término del glosario o un concepto.

- de *todos* → a `glossary_term`, `concept`

## provenance

### `derived_from` (se derivó de)

Procedencia entre nodos; la page o comentario de origen va en sources[], no en la arista.

- de *todos* → a *todos*

### `see_also` (véase también) — solo manual

Enlace manual o importado; prohibido auto-relacionar por similitud.

- de *todos* → a *todos*
