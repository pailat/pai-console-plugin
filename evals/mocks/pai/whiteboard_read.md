---
expect:
  organizationId: string
  projectId: string
  path: string
---

{"page":{"id":"5b7c9d1e-2f3a-4b5c-8d6e-7f8091a2b3c4","shortId":"wb7c9d1e","path":"{{input.path}}","title":"Flujo de ventas","audience":"internal"},"revision":7,"url":"/acme-qa/tienda-en-linea/resources/{{input.path}}","summary":{"nodes":[{"id":"lead","label":"Lead","shape":"ellipse"},{"id":"calificacion","label":"Calificación","shape":"rectangle"},{"id":"cotizacion","label":"Cotización","shape":"rectangle"}],"edges":[{"from":"lead","to":"calificacion"},{"from":"calificacion","to":"cotizacion"}],"groups":[],"texts":["Revisar con dirección comercial"],"otherCount":4},"preview":{"width":760,"height":220,"shapes":[],"omitted":0},"warnings":[],"assets":[]}
