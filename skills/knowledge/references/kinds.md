# Kinds de Conocimiento

> Generado por `tools/gen-references.ts` desde pai-portal `dfc02d78` (2026-10-11 merge: mcp-pages @45e2e4f0 (#169: page_update con título y descripción, page_move reescribe URLs absolutas del Portal, escrituras y page_list compactos, filtros de DataTable por celda)), `packages/contracts/src/knowledge`. No editar a mano: regenerar.

Cada kind tiene una plantilla estricta: una clave que no aparece aquí se rechaza. `properties` lleva exactamente estas claves. Las secciones `refs` materializan aristas al guardar.

## Heurística para clasificar

1. ¿Es una afirmación sobre el mundo o sobre lo que debe ser? → decision, business_rule, constraint, fact, objective.
2. ¿Es una receta para actuar? → flow (si es del producto), pattern, runbook.
3. ¿Es un aviso de fallo? → risk, gotcha, antipattern.
4. ¿Es intención futura o pregunta abierta? → task, question, assumption.
Si nada encaja: note (afirmación suelta), concept (definición), reference (fuente externa).
Los kinds estructurales (module, screen, flow, data_model, entity, component, actor, glossary_term) se eligen por lo que describen, no por estas preguntas.

Formato de cita: kb:<kind>/<slug>@r<revision>

## Estados

- `draft` (Borrador): Borrador: en elaboración, no cuenta como conocimiento vigente.
- `proposed` (Propuesto): Propuesto: creado por un agente en un kind decidido por humanos; pendiente de confirmación.
- `active` (Vigente): Vigente: conocimiento confirmado que los agentes deben respetar.
- `resolved` (Resuelto): Resuelto: pregunta, supuesto, riesgo o tarea cerrada con un nodo de resolución.
- `superseded` (Reemplazado): Reemplazado por otro nodo del mismo kind (histórico).
- `archived` (Archivado): Archivado: fuera del recall por defecto; reversible.
- `rejected` (Rechazado): Rechazado por una persona; conserva el motivo en properties.rejection.

## Índice

| kind | etiqueta | grupo | decide una persona | se resuelve | identificador |
|---|---|---|---|---|---|
| `objective` | Objetivo | decisiones | sí | no | `^OBJ-\d{2}$` |
| `decision` | Decisión | decisiones | sí | no | `^DEC-\d{3}$` |
| `adr` | ADR | decisiones | sí | no | `^ADR-\d{4}$` (obligatorio) |
| `business_rule` | Regla de negocio | decisiones | sí | no | `^RN-\d{2,3}$` (obligatorio) |
| `constraint` | Restricción | decisiones | sí | no | — |
| `risk` | Riesgo | evidencia | no | sí | — |
| `question` | Pregunta abierta | evidencia | no | sí | — |
| `assumption` | Supuesto | evidencia | no | sí | — |
| `task` | Tarea | evidencia | no | sí | — |
| `pattern` | Patrón | decisiones | no | no | — |
| `runbook` | Runbook | decisiones | no | no | — |
| `gotcha` | Gotcha | decisiones | no | no | — |
| `antipattern` | Antipatrón | decisiones | no | no | — |
| `note` | Nota | evidencia | no | no | — |
| `concept` | Concepto | decisiones | no | no | — |
| `fact` | Hecho | evidencia | no | no | — |
| `reference` | Referencia externa | evidencia | no | no | — |
| `module` | Módulo | estructura | no | no | `^MOD-\d{2}$` |
| `screen` | Pantalla | estructura | no | no | — |
| `flow` | Flujo | estructura | no | no | — |
| `data_model` | Modelo de datos (ERD) | estructura | no | no | — |
| `entity` | Entidad (ERD) | estructura | no | no | — |
| `component` | Componente (C4) | estructura | no | no | — |
| `actor` | Actor | estructura | no | no | — |
| `glossary_term` | Término | estructura | no | no | — |

## `objective` — Objetivo (plantilla v1)

Objetivo de negocio medible con horizonte y métrica. Decidido por humanos; un agente sólo lo propone.

Estados: `draft`, `proposed`, `active`, `superseded`, `archived`, `rejected`.

- `statement` (**obligatorio**; markdown; ≤600): Qué se quiere lograr y para quién.
- `metric` (**obligatorio**; table; columnas: name, unit, baseline, target): Una métrica con línea base y meta.
- `horizon` (**obligatorio**; date): Fecha límite (AAAA-MM-DD).
- `priority` (opcional; enum; must|should|could): must, should o could.
- `rationale` (opcional; markdown; ≤1500): Por qué importa.
- `owner` (opcional; text): Quién responde por el objetivo.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "identifier": "OBJ-01",
 "statement": "Que cada agente que actúe sobre un proyecto lo haga con el contexto vigente de sus decisiones y reglas.",
 "metric": [
  {
   "name": "Acciones de agente con bundle de contexto",
   "unit": "%",
   "baseline": "0",
   "target": "95"
  }
 ],
 "horizon": "2026-12-31",
 "priority": "must",
 "owner": "Equipo Pai"
}
```

## `decision` — Decisión (plantilla v1)

Decisión de producto o técnica en formato Nygard: contexto, decisión, consecuencias y alternativas. Decidida por humanos; un agente sólo la propone.

Estados: `draft`, `proposed`, `active`, `superseded`, `archived`, `rejected`.

- `context` (**obligatorio**; markdown; ≤3000): Qué situación obliga a decidir.
- `decision` (**obligatorio**; markdown; ≤1500): Qué se decidió, en afirmativo.
- `consequences` (**obligatorio**; table; columnas: sign, text): Al menos una positiva y una negativa.
- `decidedBy` (**obligatorio**; text): Persona o comité que decidió.
- `decidedAt` (**obligatorio**; date): AAAA-MM-DD.
- `alternatives` (opcional; table; columnas: name, rejectedBecause): Qué más se consideró y por qué no.
- `reviewBy` (opcional; date): Fecha de revisión.
- `affects` (opcional; refs; → arista `affects`): Nodos que esta decisión impacta.
- `contributes_to` (opcional; refs; → arista `contributes_to` a objective): Objetivos a los que sirve.
- `grounds` (opcional; refs; → arista `grounds` a fact/reference/note/concept): Hechos y referencias que la fundamentan.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "context": "Los agentes pueden proponer decisiones, pero el equipo quiere que ninguna entre en vigor sin revisión humana.",
 "decision": "Los agentes crean objetivos, decisiones, ADRs, reglas y restricciones en estado proposed; una persona de Pai los confirma desde la UI.",
 "consequences": [
  {
   "sign": "positive",
   "text": "Ningún conocimiento normativo nace sin revisión."
  },
  {
   "sign": "negative",
   "text": "Las propuestas pueden acumularse si nadie las revisa."
  }
 ],
 "decidedBy": "Alejandro Sánchez",
 "decidedAt": "2026-09-07",
 "alternatives": [
  {
   "name": "Confianza total en el agente",
   "rejectedBecause": "Un error del modelo se convertiría en regla vigente."
  }
 ],
 "affects": [
  "module/knowledge"
 ]
}
```

## `adr` — ADR (plantilla v1)

Architecture Decision Record en formato MADR 4: contexto, opciones consideradas, resultado y consecuencias. Decidido por humanos; un agente sólo lo propone.

Estados: `draft`, `proposed`, `active`, `superseded`, `archived`, `rejected`.

- `deciders` (**obligatorio**; list): Personas que tomaron la decisión.
- `date` (**obligatorio**; date): Fecha de la decisión (AAAA-MM-DD).
- `mode` (opcional; enum; madr|lightweight): madr (completo) o lightweight.
- `context` (**obligatorio**; markdown; ≤4000): Qué situación obliga a decidir y qué fuerzas están en juego.
- `drivers` (opcional; list): Criterios que pesan en la elección.
- `options` (**obligatorio**; table; columnas: name, description, pros, cons): Al menos dos opciones con pros y contras.
- `outcome` (**obligatorio**; markdown; ≤1500): Opción elegida (nombrada literalmente) y por qué.
- `consequences` (**obligatorio**; table; columnas: sign, text): Al menos una positiva y una negativa.
- `confirmation` (opcional; markdown; ≤1500): Cómo se comprobará que la decisión se cumple.
- `more` (opcional; markdown; ≤2000): Enlaces y detalles.
- `affects` (opcional; refs; → arista `affects`): Nodos que esta decisión impacta.
- `contributes_to` (opcional; refs; → arista `contributes_to` a objective): Objetivos a los que sirve.
- `grounds` (opcional; refs; → arista `grounds` a fact/reference/note/concept): Hechos, referencias, notas o conceptos que fundamentan el ADR.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "identifier": "ADR-0026",
 "deciders": [
  "Alejandro Sánchez"
 ],
 "date": "2026-09-07",
 "mode": "madr",
 "context": "El Portal necesita un grafo de conocimiento por proyecto consultable por agentes con garantías multi-tenant y sin añadir infraestructura nueva.",
 "drivers": [
  "Aislamiento por organización",
  "Coste operativo",
  "SQL/PGQ en PG19"
 ],
 "options": [
  {
   "name": "Grafo en Postgres con SQL/PGQ",
   "description": "Tablas de nodos y aristas más un property graph.",
   "pros": [
    "Misma base y mismas políticas RLS",
    "Sin nuevo servicio"
   ],
   "cons": [
    "Sin caminos de longitud variable en 19"
   ]
  },
  {
   "name": "Base de grafos dedicada",
   "description": "Neo4j u otro motor externo.",
   "pros": [
    "Cypher completo"
   ],
   "cons": [
    "Nueva infraestructura",
    "Duplicar el modelo de tenants"
   ]
  }
 ],
 "outcome": "Elegimos Grafo en Postgres con SQL/PGQ porque conserva RLS y evita un servicio nuevo; las consultas transitivas usan CTE acotadas.",
 "consequences": [
  {
   "sign": "positive",
   "text": "Un solo motor y una sola política de aislamiento."
  },
  {
   "sign": "negative",
   "text": "Los recorridos de profundidad variable se implementan a mano con CTE."
  }
 ],
 "affects": [
  "module/knowledge"
 ],
 "contributes_to": [
  "objective/obj-01-contexto-confiable-para-agentes"
 ]
}
```

## `business_rule` — Regla de negocio (plantilla v1)

Regla operativa con modalidad (obligación, prohibición, permiso o cálculo), condición, acción, ejemplos y a qué aplica. Una regla que no aplica a nada es una nota.

Estados: `draft`, `proposed`, `active`, `superseded`, `archived`, `rejected`.

- `modality` (**obligatorio**; enum; obligation|prohibition|permission|computation): obligation, prohibition, permission o computation.
- `statement` (**obligatorio**; text; ≤600): Una frase con el verbo modal: «… debe …», «… no debe …», «… puede …», «… se calcula …».
- `given` (**obligatorio**; text; ≤600): Condición bajo la que aplica.
- `then` (**obligatorio**; text; ≤600): Qué ocurre o qué se exige.
- `rationale` (**obligatorio**; markdown; ≤1500): Por qué existe la regla.
- `examples` (**obligatorio**; table; columnas: case, expected, valid): Casos válidos e inválidos.
- `exceptions` (opcional; list): Situaciones en que no aplica.
- `enforcement` (**obligatorio**; enum; ui|api|database|manual): ui, api, database o manual (varios).
- `severity` (**obligatorio**; enum; low|medium|high): low, medium o high.
- `applies_to` (**obligatorio**; refs; → arista `constrains` a module/screen/flow/entity/component/decision/adr): Módulos, pantallas, flujos, entidades o decisiones que restringe.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "identifier": "RN-01",
 "modality": "obligation",
 "statement": "Un miembro cliente sólo debe leer nodos de Knowledge con visibilidad client.",
 "given": "El usuario pertenece a la organización pero no es staff de la plataforma.",
 "then": "Las consultas se ejecutan con app.knowledge_client_scope = on y sólo devuelven nodos client.",
 "rationale": "Los riesgos, decisiones internas y notas del equipo no forman parte de lo comunicado al cliente.",
 "examples": [
  {
   "case": "Miembro cliente lista nodos",
   "expected": "Sólo nodos client",
   "valid": true
  },
  {
   "case": "Miembro cliente lee un riesgo internal",
   "expected": "NOT_FOUND",
   "valid": false
  }
 ],
 "enforcement": [
  "database",
  "api"
 ],
 "severity": "high",
 "applies_to": [
  "module/knowledge",
  "screen/knowledge-lista"
 ]
}
```

## `constraint` — Restricción (plantilla v1)

Límite externo o interno que el proyecto no elige (técnico, legal, de negocio u organizativo). Decidida por humanos; un agente sólo la propone.

Estados: `draft`, `proposed`, `active`, `superseded`, `archived`, `rejected`.

- `statement` (**obligatorio**; markdown; ≤4000): La afirmación, en una o pocas frases.
- `rationale` (opcional; markdown; ≤2000): Por qué se sostiene; su ausencia marca el nodo como delgado.
- `details` (opcional; markdown; ≤8000): Desarrollo, matices, ejemplos.
- `origin` (**obligatorio**; enum; technical|legal|business|organizational): technical, legal, business u organizational.
- `constrains` (opcional; refs; → arista `constrains` a module/screen/flow/entity/component/decision/adr): Qué partes del proyecto limita.
- `refers_to` (opcional; refs; → arista `refers_to` a glossary_term/concept): Términos del glosario o conceptos que usa.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "statement": "PostgreSQL 19 no soporta caminos de longitud variable en SQL/PGQ; los recorridos transitivos se implementan con CTE recursivas acotadas.",
 "rationale": "Verificado en 19beta3: los cuantificadores de camino no están implementados.",
 "origin": "technical",
 "constrains": [
  "module/knowledge"
 ]
}
```

## `risk` — Riesgo (plantilla v1)

Riesgo con probabilidad e impacto (1..5), exposición derivada, mitigación y señales de alerta. Se resuelve con knowledge_resolve (confirmed = mitigado, refuted = materializado).

Estados: `draft`, `active`, `resolved`, `superseded`, `archived`.

- `description` (**obligatorio**; markdown; ≤2000): Qué puede salir mal y por qué.
- `likelihood` (**obligatorio**; number): 1 (rara) a 5 (casi segura).
- `impact` (**obligatorio**; number): 1 (menor) a 5 (crítico).
- `mitigation` (**obligatorio**; markdown; ≤1500): Qué se hace para reducirlo.
- `owner` (opcional; text): Quién vigila el riesgo.
- `signals` (opcional; list): Indicios de que se está materializando.
- `threatens` (opcional; refs; → arista `threatens` a objective/module/screen/flow/entity/component): Objetivos o partes de la estructura amenazadas.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "description": "Una consulta GRAPH_TABLE sin project_id explícito en el primer vértice podría cruzar datos de otro proyecto de la misma organización.",
 "likelihood": 2,
 "impact": 5,
 "mitigation": "Todas las consultas del catálogo fijan project_id en el primer vértice y los tests de RLS cubren GRAPH_TABLE.",
 "owner": "Equipo Pai",
 "signals": [
  "Un test de aislamiento devuelve filas de otro proyecto"
 ],
 "threatens": [
  "objective/obj-03-aislamiento-multi-tenant"
 ]
}
```

## `question` — Pregunta abierta (plantilla v1)

Pregunta sin respuesta todavía. Se cierra con knowledge_resolve (answered) creando o enlazando el nodo que la responde.

Estados: `draft`, `active`, `resolved`, `superseded`, `archived`.

- `statement` (**obligatorio**; markdown; ≤4000): La afirmación, en una o pocas frases.
- `rationale` (opcional; markdown; ≤2000): Por qué se sostiene; su ausencia marca el nodo como delgado.
- `details` (opcional; markdown; ≤8000): Desarrollo, matices, ejemplos.
- `askedBy` (opcional; text): Quién la planteó.
- `refers_to` (opcional; refs; → arista `refers_to` a glossary_term/concept): Términos del glosario o conceptos que usa.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "statement": "¿Añadimos una FK de knowledge_node.page_id a page tras el merge con Pages?",
 "rationale": "Hoy la referencia es blanda para no acoplar ramas.",
 "askedBy": "Alejandro Sánchez"
}
```

## `assumption` — Supuesto (plantilla v1)

Algo que se da por cierto sin haberlo comprobado. Se cierra con knowledge_resolve (confirmed o refuted).

Estados: `draft`, `active`, `resolved`, `superseded`, `archived`.

- `statement` (**obligatorio**; markdown; ≤4000): La afirmación, en una o pocas frases.
- `rationale` (opcional; markdown; ≤2000): Por qué se sostiene; su ausencia marca el nodo como delgado.
- `details` (opcional; markdown; ≤8000): Desarrollo, matices, ejemplos.
- `validation` (opcional; text; ≤600): Experimento o dato que lo confirmaría.
- `refers_to` (opcional; refs; → arista `refers_to` a glossary_term/concept): Términos del glosario o conceptos que usa.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "statement": "Un nodo de Knowledge cabe entero en un embedding de 8000 caracteres sin perder recall.",
 "validation": "Medir recall de búsqueda con nodos largos frente a chunking por encabezados."
}
```

## `task` — Tarea (plantilla v2)

Intención de trabajo futuro ligada al conocimiento del proyecto. Se cierra con knowledge_resolve (done o wont_do).

Estados: `draft`, `active`, `resolved`, `superseded`, `archived`.

- `statement` (**obligatorio**; markdown; ≤4000): La afirmación, en una o pocas frases.
- `rationale` (opcional; markdown; ≤2000): Por qué se sostiene; su ausencia marca el nodo como delgado.
- `details` (opcional; markdown; ≤8000): Desarrollo, matices, ejemplos.
- `owner` (opcional; text): Quién la ejecuta.
- `startDate` (opcional; date): AAAA-MM-DD.
- `dueDate` (opcional; date): AAAA-MM-DD.
- `milestoneId` (opcional; milestone): Hito del proyecto al que contribuye.
- `refers_to` (opcional; refs; → arista `refers_to` a glossary_term/concept): Términos del glosario o conceptos que usa.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "statement": "Mover el GRANT del property graph a scripts/setup-db-roles.ts tras el merge.",
 "owner": "Equipo Pai",
 "startDate": "2026-09-28",
 "dueDate": "2026-10-01"
}
```

## `pattern` — Patrón (plantilla v1)

Receta reutilizable: contexto, problema, solución y consecuencias.

Estados: `draft`, `active`, `superseded`, `archived`.

- `context` (**obligatorio**; markdown; ≤1500): Cuándo aplica.
- `problem` (**obligatorio**; markdown; ≤1500): Qué resuelve.
- `solution` (**obligatorio**; markdown; ≤3000): Cómo se aplica.
- `consequences` (**obligatorio**; table; columnas: sign, text): Efectos positivos y negativos.
- `examples` (opcional; list): Dónde se usa.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "context": "Consultas de vecindario sobre el grafo de conocimiento.",
 "problem": "Los patrones no dirigidos en GRAPH_TABLE son hasta 240 veces más lentos.",
 "solution": "Escribir siempre patrones dirigidos y unir ambas direcciones con UNION ALL.",
 "consequences": [
  {
   "sign": "positive",
   "text": "Consultas de vecinos en menos de un milisegundo a escala."
  },
  {
   "sign": "neutral",
   "text": "Cada consulta duplica el texto del patrón."
  }
 ],
 "examples": [
  "Q1 vecinos a 1 salto",
  "Q3 segundo anillo"
 ]
}
```

## `runbook` — Runbook (plantilla v1)

Procedimiento operativo paso a paso con precondiciones, comandos y vuelta atrás.

Estados: `draft`, `active`, `superseded`, `archived`.

- `when` (**obligatorio**; text; ≤300): Situación que dispara el procedimiento.
- `preconditions` (opcional; list): Qué debe cumplirse antes.
- `steps` (**obligatorio**; table; columnas: n, action, expected, command): Numerados 1..n, con resultado esperado y comando.
- `rollback` (opcional; markdown; ≤1500): Cómo deshacer.
- `mitigates` (opcional; refs; → arista `mitigates` a risk): Riesgos que este runbook mitiga.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "when": "Hay que alterar o eliminar una columna expuesta en el property graph knowledge_graph.",
 "preconditions": [
  "Ventana de mantenimiento",
  "Backup reciente"
 ],
 "steps": [
  {
   "n": 1,
   "action": "Abrir transacción",
   "command": "BEGIN;"
  },
  {
   "n": 2,
   "action": "Eliminar el grafo",
   "command": "DROP PROPERTY GRAPH knowledge_graph;"
  },
  {
   "n": 3,
   "action": "Alterar la columna",
   "expected": "ALTER TABLE termina sin error"
  },
  {
   "n": 4,
   "action": "Recrear el grafo con el CREATE PROPERTY GRAPH literal de la migración 2 y el GRANT"
  },
  {
   "n": 5,
   "action": "Confirmar",
   "command": "COMMIT;"
  }
 ],
 "rollback": "ROLLBACK; el grafo original sigue existiendo."
}
```

## `gotcha` — Gotcha (plantilla v1)

Trampa no obvia: síntoma, causa y forma de sortearla.

Estados: `draft`, `active`, `superseded`, `archived`.

- `symptom` (**obligatorio**; markdown; ≤1000): Qué se observa.
- `cause` (**obligatorio**; markdown; ≤1500): Por qué ocurre.
- `workaround` (**obligatorio**; markdown; ≤1500): Qué hacer.
- `affects` (opcional; refs; → arista `affects`): Nodos afectados.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "symptom": "GRAPH_TABLE falla con «permission denied for property graph» desde app_user.",
 "cause": "Un property graph es relkind g: GRANT ON ALL TABLES y ALTER DEFAULT PRIVILEGES no lo cubren.",
 "workaround": "Ejecutar GRANT SELECT ON PROPERTY GRAPH knowledge_graph TO app_user (bun run knowledge:grant-graph)."
}
```

## `antipattern` — Antipatrón (plantilla v1)

Práctica que parece razonable y causa daño: síntoma, por qué es mala y qué hacer en su lugar.

Estados: `draft`, `active`, `superseded`, `archived`.

- `symptom` (**obligatorio**; markdown; ≤1500): Cómo se reconoce.
- `whyBad` (**obligatorio**; markdown; ≤1500): Qué daño causa.
- `instead` (**obligatorio**; markdown; ≤1500): Qué hacer.
- `seenIn` (opcional; refs; → arista `affects`): Nodos donde se ha detectado.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "symptom": "Aristas see_also creadas automáticamente por similitud de embeddings.",
 "whyBad": "En CKL 27 átomos produjeron 130 aristas, 120 de ellas ruido; el grafo pierde señal.",
 "instead": "Sólo enlaces manuales o importados; la similitud se usa para sugerir, no para relacionar."
}
```

## `note` — Nota (plantilla v1)

Afirmación suelta que no encaja en otro kind.

Estados: `draft`, `active`, `superseded`, `archived`.

- `statement` (**obligatorio**; markdown; ≤4000): La afirmación, en una o pocas frases.
- `rationale` (opcional; markdown; ≤2000): Por qué se sostiene; su ausencia marca el nodo como delgado.
- `details` (opcional; markdown; ≤8000): Desarrollo, matices, ejemplos.
- `refers_to` (opcional; refs; → arista `refers_to` a glossary_term/concept): Términos del glosario o conceptos que usa.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "statement": "El módulo Pages vive en lib/pages y components/pages."
}
```

## `concept` — Concepto (plantilla v1)

Definición de una idea del dominio, más amplia que un término de glosario.

Estados: `draft`, `active`, `superseded`, `archived`.

- `statement` (**obligatorio**; markdown; ≤4000): La afirmación, en una o pocas frases.
- `rationale` (opcional; markdown; ≤2000): Por qué se sostiene; su ausencia marca el nodo como delgado.
- `details` (opcional; markdown; ≤8000): Desarrollo, matices, ejemplos.
- `aliases` (opcional; list): Otros nombres con los que se conoce.
- `refers_to` (opcional; refs; → arista `refers_to` a glossary_term/concept): Términos del glosario o conceptos que usa.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "statement": "Un bundle de contexto es el texto acotado y citado que un agente recibe antes de actuar sobre un nodo.",
 "aliases": [
  "context bundle"
 ]
}
```

## `fact` — Hecho (plantilla v1)

Dato verificable con al menos una fuente en sources. Sirve como grounds o supports de decisiones y reglas.

Estados: `draft`, `active`, `superseded`, `archived`.

- `statement` (**obligatorio**; markdown; ≤4000): La afirmación, en una o pocas frases.
- `rationale` (opcional; markdown; ≤2000): Por qué se sostiene; su ausencia marca el nodo como delgado.
- `details` (opcional; markdown; ≤8000): Desarrollo, matices, ejemplos.
- `observedAt` (opcional; date): AAAA-MM-DD.
- `refers_to` (opcional; refs; → arista `refers_to` a glossary_term/concept): Términos del glosario o conceptos que usa.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "statement": "SQL/PGQ en PostgreSQL 19beta3 no implementa cuantificadores de camino; sólo patrones de profundidad fija.",
 "observedAt": "2026-09-07"
}
```

## `reference` — Referencia externa (plantilla v1)

Fuente externa (especificación, artículo, repositorio, estándar) resumida. El servicio añade la URL a sources si falta.

Estados: `draft`, `active`, `superseded`, `archived`.

- `url` (**obligatorio**; text; ≤1000): Dirección de la fuente.
- `title` (**obligatorio**; text; ≤200): Título de la fuente.
- `kindOfSource` (**obligatorio**; enum; spec|paper|article|repo|standard|other): spec, paper, article, repo, standard u other.
- `accessedAt` (**obligatorio**; date): AAAA-MM-DD.
- `summary` (**obligatorio**; markdown; ≤2000): Qué aporta la fuente al proyecto.
- `documents` (opcional; refs; → arista `documents`): Nodos que esta fuente documenta.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "url": "https://www.postgresql.org/docs/19/sql-createpropertygraph.html",
 "title": "CREATE PROPERTY GRAPH — PostgreSQL 19 documentation",
 "kindOfSource": "spec",
 "accessedAt": "2026-09-07",
 "summary": "Sintaxis y limitaciones del property graph nativo en PostgreSQL 19.",
 "documents": [
  "module/knowledge"
 ]
}
```

## `module` — Módulo (plantilla v1)

Área funcional del producto: responsabilidad, qué entra y qué queda fuera, rutas de código y partes que contiene.

Estados: `draft`, `active`, `superseded`, `archived`.

- `responsibility` (**obligatorio**; markdown; ≤1500): Qué hace el módulo y para quién.
- `scopeIn` (**obligatorio**; list): Qué cubre.
- `scopeOut` (**obligatorio**; list): Qué NO cubre (obligatorio).
- `owner` (opcional; text): Equipo o persona.
- `codePaths` (opcional; list): Directorios o archivos del repositorio.
- `contains` (opcional; refs; → arista `contains` a module/screen/flow/entity/component): Pantallas, flujos, entidades, componentes o submódulos.
- `dependsOn` (opcional; refs; → arista `depends_on` a module/component/entity): Módulos, componentes o entidades necesarios.
- `contributes_to` (opcional; refs; → arista `contributes_to` a objective): Objetivos a los que sirve.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "identifier": "MOD-05",
 "responsibility": "Grafo de conocimiento por proyecto: nodos tipados, aristas con evidencia, bundles de contexto para agentes y wiki con plantillas.",
 "scopeIn": [
  "Nodos y aristas",
  "Búsqueda híbrida",
  "Bundles para agentes"
 ],
 "scopeOut": [
  "Edición colaborativa",
  "Runtime de Apps"
 ],
 "owner": "Equipo Pai",
 "codePaths": [
  "lib/knowledge",
  "components/knowledge"
 ],
 "contains": [
  "screen/knowledge-lista",
  "entity/knowledge-node"
 ],
 "dependsOn": [
  "module/projects"
 ]
}
```

## `screen` — Pantalla (plantilla v1)

Pantalla del producto: ruta, propósito, actores, estados, bloques de contenido, acciones, reglas que la restringen y navegación.

Estados: `draft`, `active`, `superseded`, `archived`.

- `route` (**obligatorio**; text; ≤300): Ruta o patrón de URL.
- `purpose` (**obligatorio**; markdown; ≤1500): Para qué existe y qué decide el usuario aquí.
- `actors` (**obligatorio**; refs; → arista `performs` a actor): Quién la usa (al menos uno).
- `states` (**obligatorio**; list): Al menos dos: vacío, carga, error, sin permisos…
- `content` (**obligatorio**; table; columnas: block, data, source): Bloques y de dónde salen sus datos.
- `actions` (**obligatorio**; table; columnas: action, effect, rule): Qué puede hacer el usuario y con qué efecto.
- `rules` (opcional; refs; → arista `constrains` a business_rule/constraint): Reglas y restricciones aplicables.
- `uses` (opcional; refs; → arista `uses` a entity/component): Entidades y componentes que usa.
- `navigatesTo` (opcional; refs; → arista `navigates_to` a screen): Pantallas alcanzables.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "route": "/organization/projects/[projectId]/knowledge",
 "purpose": "Listar y filtrar los nodos de Knowledge del proyecto y abrir su detalle.",
 "actors": [
  "actor/staff-pai",
  "actor/miembro-cliente"
 ],
 "states": [
  "vacío",
  "carga",
  "error",
  "sin permisos"
 ],
 "content": [
  {
   "block": "Tabla de nodos",
   "data": "título, estado, capa, visibilidad",
   "source": "knowledge.list"
  }
 ],
 "actions": [
  {
   "action": "Nuevo nodo",
   "effect": "Abre el formulario por kind",
   "rule": "business_rule/rn-02-solo-staff-escribe"
  }
 ],
 "uses": [
  "entity/knowledge-node"
 ],
 "navigatesTo": [
  "screen/knowledge-detalle"
 ]
}
```

## `flow` — Flujo (plantilla v1)

Flujo del producto: disparador, resultado, pasos numerados con actor, pantalla y regla, y caminos alternativos. El diagrama se genera desde los pasos.

Estados: `draft`, `active`, `superseded`, `archived`.

- `trigger` (**obligatorio**; text; ≤300): Qué inicia el flujo.
- `outcome` (**obligatorio**; text; ≤300): Qué queda al terminar.
- `summary` (**obligatorio**; markdown; ≤1500): El flujo en pocas frases.
- `steps` (**obligatorio**; table; columnas: n, actor, action, screen, result, rule): Numerados 1..n con actor, acción, pantalla, resultado y regla.
- `alternatives` (opcional; table; columnas: when, then): Caminos alternativos o de error.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "trigger": "Un hilo de comentarios en una Page termina en una aceptación o corrección.",
 "outcome": "Existe un nodo decision con la fuente del comentario y estado proposed o active.",
 "summary": "El staff registra la decisión desde el hilo; el formulario se prellena con la cita y el nodo queda enlazado a la Page.",
 "steps": [
  {
   "n": 1,
   "actor": "actor/staff-pai",
   "action": "Pulsa «Registrar como decisión» en el hilo",
   "screen": "screen/page-lectura",
   "result": "Se abre el formulario con sources[0] prellenado"
  },
  {
   "n": 2,
   "actor": "actor/staff-pai",
   "action": "Completa contexto, decisión y consecuencias",
   "screen": "screen/knowledge-editor",
   "result": "El nodo se crea con revisión 0",
   "rule": "business_rule/rn-02-solo-staff-escribe"
  }
 ],
 "alternatives": [
  {
   "when": "La plantilla falla",
   "then": "Se muestran los issues junto a cada campo."
  }
 ]
}
```

## `data_model` — Modelo de datos (ERD) (plantilla v1)

Alcance de un ERD: el conjunto de entidades de una base de datos o de un esquema. Contiene sus entidades (cada entidad declara su modelo); el diagrama entidad-relación se deriva de ellas y se proyecta en las pages.

Estados: `draft`, `active`, `superseded`, `archived`.

- `purpose` (**obligatorio**; markdown; ≤1500): Qué datos agrupa y para qué producto o servicio.
- `engine` (opcional; text; ≤80): Base de datos y versión (p. ej. PostgreSQL 19).
- `namespace` (opcional; text; ≤63): Esquema de la base (snake_case), p. ej. public.
- `conventions` (opcional; list): Reglas de nombres, claves y auditoría que siguen sus entidades.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "purpose": "Grafo de conocimiento de un proyecto: nodos, aristas y versiones con RLS por organización.",
 "engine": "PostgreSQL 19 + pgvector",
 "namespace": "public",
 "conventions": [
  "Claves primarias uuid con gen_random_uuid()",
  "organization_id y project_id en toda tabla"
 ]
}
```

## `entity` — Entidad (ERD) (plantilla v2)

Tabla del modelo de datos: columnas con tipo, nulabilidad, clave primaria, unicidad y claves foráneas. Las relaciones no se escriben: salen de las claves foráneas (cardinalidad, identificante y opcional se derivan) y se materializan como relates_to. Pertenece a un modelo de datos (dataModel). El ERD se genera.

Estados: `draft`, `active`, `superseded`, `archived`.

- `physicalName` (opcional; text; ≤63): Nombre de la tabla (snake_case).
- `dataModel` (opcional; refs; → arista `contains` a data_model): Modelo de datos (ERD) al que pertenece la entidad.
- `purpose` (**obligatorio**; markdown; ≤1500): Qué representa y por qué existe.
- `columns` (**obligatorio**; table; columnas: name, type, isArray, nullable, primaryKey, unique, enumValues, referencesEntity, referencesColumn, onDelete, default, description): Al menos una clave primaria; nombres únicos. Una clave foránea es la relación.
- `invariants` (opcional; list): Reglas que siempre se cumplen.
- `lifecycle` (opcional; markdown; ≤1500): Estados y transiciones.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "physicalName": "knowledge_edge",
 "dataModel": [
  "data_model/modelo-knowledge"
 ],
 "purpose": "Relación tipada entre dos nodos de conocimiento del mismo proyecto.",
 "columns": [
  {
   "name": "id",
   "type": "uuid",
   "nullable": false,
   "primaryKey": true,
   "unique": false,
   "default": "gen_random_uuid()"
  },
  {
   "name": "source_id",
   "type": "uuid",
   "nullable": false,
   "primaryKey": false,
   "unique": false,
   "referencesEntity": "entity/knowledge-node",
   "referencesColumn": "id",
   "onDelete": "cascade"
  },
  {
   "name": "rel",
   "type": "enum",
   "nullable": false,
   "primaryKey": false,
   "unique": false,
   "enumValues": [
    "contains",
    "depends_on",
    "relates_to"
   ]
  },
  {
   "name": "properties",
   "type": "jsonb",
   "nullable": false,
   "primaryKey": false,
   "unique": false,
   "description": "Cardinalidad y etiqueta en relates_to"
  }
 ],
 "invariants": [
  "source_id distinto de target_id"
 ]
}
```

## `component` — Componente (C4) (plantilla v3)

Elemento del modelo C4 en cualquiera de los cuatro niveles (context, container, component, code): sistema, sistema externo, contenedor (app, base de datos, cola), componente o elemento de código, con tecnología, padre (parent, nivel inmediatamente superior), relaciones descritas con su tecnología y los modelos de datos que guarda o usa. Las personas son nodos actor. Las vistas C4 se derivan.

Estados: `draft`, `active`, `superseded`, `archived`.

- `c4Level` (**obligatorio**; enum; context|container|component|code): context, container, component o code.
- `c4Type` (**obligatorio**; enum; Person|System|System_Ext|Container|ContainerDb|ContainerQueue|Component|Code): System o System_Ext (context); Container, ContainerDb, ContainerQueue o System_Ext (container); Component, ContainerDb o System_Ext (component); Code (code). Las personas son actores.
- `technology` (opcional; text; ≤80): Obligatoria en container y component (en code, el lenguaje).
- `responsibility` (**obligatorio**; markdown; ≤1000): Qué hace.
- `parent` (opcional; refs; → arista `contains` a component): Elemento C4 del nivel inmediatamente superior que lo contiene (sistema de un contenedor, contenedor de un componente).
- `relationships` (opcional; table; columnas: to, direction, description, technology): Con quién interactúa: out = este elemento usa al otro; in = el otro (o una persona/actor) lo usa. Describe qué hace y con qué tecnología.
- `dataModels` (opcional; refs; → arista `uses` a data_model): Modelos de datos (ERD) que guarda o usa.
- `stereotype` (opcional; enum; component|controller|service|repository|module|interface): Nivel component: component, controller (rutas HTTP), service (métodos), repository (entidad y operaciones), module (exports) o interface (contrato).
- `codeKind` (opcional; enum; class|interface|enum|entity|function): Nivel code: class, interface, enum, entity o function.
- `entity` (opcional; refs; → arista `uses` a entity): Repository o entidad de código: la entidad del modelo de datos que gestiona o implementa.
- `dataOperations` (opcional; list): Repository: create, read, update, delete, list o count.
- `httpRoutes` (opcional; table; columnas: method, path, handler, description): Controller o clase: método, ruta y quién la atiende.
- `methods` (opcional; table; columnas: name, parameters, returns, visibility, description): Service, interface, controller, repository, clase, interfaz o función.
- `attributes` (opcional; table; columnas: name, type, visibility, description): Clase o entidad de código.
- `enumValues` (opcional; list): Enum de código: sus valores.
- `exports` (opcional; list): Module: lo que expone.
- `interfaces` (opcional; table; columnas: name, protocol, direction, description): Entradas y salidas con protocolo.
- `operations` (opcional; markdown; ≤1500): Despliegue, escalado, observabilidad.
- `codePaths` (opcional; list): Directorios o archivos.
- `dependsOn` (opcional; refs; → arista `depends_on` a module/component/entity): Módulos, componentes o entidades.
- `uses` (opcional; refs; → arista `uses` a entity/component): Entidades y componentes.
- `implements` (opcional; refs; → arista `implements` a business_rule/decision/adr/objective/pattern/runbook): Reglas, decisiones, ADRs, objetivos, patrones o runbooks.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "c4Level": "container",
 "c4Type": "ContainerDb",
 "technology": "PostgreSQL 19 + pgvector",
 "responsibility": "Almacena nodos, aristas, versiones y el property graph de Knowledge con RLS por organización.",
 "interfaces": [
  {
   "name": "SQL",
   "protocol": "libpq",
   "direction": "in",
   "description": "Consultas desde el Portal"
  }
 ],
 "parent": [
  "component/cmp-pai-portal"
 ],
 "relationships": [
  {
   "to": "component/cmp-portal-next",
   "direction": "in",
   "description": "Lee y escribe nodos y aristas",
   "technology": "SQL/TLS"
  }
 ],
 "dataModels": [
  "data_model/modelo-knowledge"
 ],
 "codePaths": [
  "lib/db/migrations"
 ]
}
```

## `actor` — Actor (plantilla v1)

Persona, rol, sistema o agente que interactúa con el producto: qué quiere lograr y qué puede hacer.

Estados: `draft`, `active`, `superseded`, `archived`.

- `actorType` (**obligatorio**; enum; person|role|system|agent): person, role, system o agent.
- `description` (**obligatorio**; markdown; ≤1000): Quién es.
- `goals` (**obligatorio**; list): Qué quiere conseguir (al menos uno).
- `portalRole` (opcional; enum; owner|admin|member|staff|anonymous|none): owner, admin, member, staff, anonymous o none.
- `permissions` (opcional; list): Qué puede hacer.
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "actorType": "role",
 "description": "Persona del equipo Pai con rol de plataforma admin; gestiona proyectos y confirma conocimiento.",
 "goals": [
  "Mantener el grafo del proyecto vigente",
  "Confirmar o rechazar propuestas de agentes"
 ],
 "portalRole": "staff",
 "permissions": [
  "Crear y editar nodos",
  "Enlazar y archivar"
 ]
}
```

## `glossary_term` — Término (plantilla v1)

Término del glosario del proyecto: definición corta, alias, con qué no confundirlo y ejemplo.

Estados: `draft`, `active`, `superseded`, `archived`.

- `definition` (**obligatorio**; markdown; ≤1500): Qué significa en este proyecto.
- `aliases` (opcional; list): Sinónimos aceptados.
- `notThis` (opcional; list): Términos parecidos que significan otra cosa.
- `example` (opcional; text; ≤300): Uso en una frase.
- `sourceOfTruth` (opcional; text; ≤160): Nodo que define el término (informativo).
- `notes` (opcional; markdown; ≤2000): Observaciones adicionales que no encajan en otra sección.

Ejemplo de `properties`:

```json
{
 "definition": "Documento de comunicación a humanos dentro de un proyecto; proyección del grafo, nunca fuente.",
 "aliases": [
  "Page"
 ],
 "notThis": [
  "artifact"
 ],
 "example": "La decisión vive en Knowledge y se comunica en una Page."
}
```
