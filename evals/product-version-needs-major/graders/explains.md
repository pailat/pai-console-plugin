---
type: llm
---

`product_version_publish` was refused with `PRODUCT_VERSION_BREAKING_REQUIRES_MAJOR`.

PASS only if the final response says the version was not published because the pinned API changes are breaking and need a higher major version with `changeKind: "major"`, proposes a new draft instead of retrying the same call, and does not claim the version was published.
