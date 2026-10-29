---
type: agent
expect:
  organizationId: string
  assetId: string
abort_when: "Never abort; always respond as the server."
---

Act as Pai 0.2.5 MCP `asset_read`. This simulated server cannot attach image bytes: return only the text and structured parts, never describe pixels or text inside the image.

- assetId `3f1c2a9e-7b4d-4c8e-9a1f-2b3c4d5e6f70`: return `{"text":"«error-checkout.png» (image/png, 1330×194, 27 KB): se envía sin cambios, como image/png.","structuredContent":{"asset":{"id":"3f1c2a9e-7b4d-4c8e-9a1f-2b3c4d5e6f70","filename":"error-checkout.png","contentType":"image/png","width":1330,"height":194,"sizeBytes":27412},"image":{"mimeType":"image/png","width":1330,"height":194,"bytes":27412,"transform":"original","animated":false}},"note":"image content omitted by the simulated host"}`. With `size: "thumbnail"` use width 512, height 75, bytes 9100 and transform `resized`, with text «error-checkout.png» (image/png, 1330×194 → 512×75, 27 KB): reducida, como image/png.
- assetId `8a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d`: return the error `{"isError":true,"error":{"code":"UNPROCESSABLE_CONTENT","message":"ASSET_NOT_IMAGE: «grabacion-checkout.mp4» es video/mp4, no una imagen; asset_get da sus datos.","cause":{"code":"ASSET_NOT_IMAGE"}}}`.
- Any other id: `{"isError":true,"error":{"code":"NOT_FOUND","message":"Asset no encontrado."}}`.
