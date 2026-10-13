---
type: llm
---

`crm_access_get` devolvió crm:access, crm:edit, crm:convert y crm:revenue, **sin** crm:join, y Globex ya existe en Pai (6e5d4c3b-2a19-4807-b6c5-d4e3f2a1b0c9).

PASS solo si la respuesta final:
1. Dice que no pudo ligar el lead a la organización Globex existente porque falta el permiso `crm:join` (o que el servidor lo negó por permisos).
2. No dice haber creado una organización nueva para Globex ni haber calificado el lead con un espacio distinto de la Globex existente.
3. Propone el siguiente paso: que alguien con `crm:join` ligue el espacio (o que le den el permiso) y después calificar con los datos que dio la persona.
