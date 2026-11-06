# Knowledge target

The distiller writes a knowledge delta into Pai Knowledge. It needs to be told where, so the project config names the target. Without a target the distiller fails closed and writes nothing.

## Config

```toml
[knowledge]
organization = "acme"        # required
project = "acme-app"         # exactly one of project or product

[knowledge.streams.main]     # optional override for one stream
product = "acme-storefront"  # organization is inherited from [knowledge]
```

- `organization` is required on `[knowledge]`; a stream may set its own, otherwise it inherits.
- Give `project` or `product`, never both and never neither. A stream override replaces the default's project or product as a whole.
- Stream names follow the rule of queue names: lowercase letters, digits, `-` and `_`, starting with a letter.
- Unknown keys and values that are not non-empty strings are rejected by `scripts/validate_config.py`.
- `examples/acme/.pai-harness.toml` shows the whole shape with fictional Acme values.

## Resolution

The launcher picks the stream from `--stream`, else from the queue name; a stream or queue with no override uses the default. An unknown `--stream` is a usage error. It then:

1. exports `PAI_HARNESS_KNOWLEDGE_ORG` and `PAI_HARNESS_KNOWLEDGE_PROJECT` or `PAI_HARNESS_KNOWLEDGE_PRODUCT` (plus `PAI_HARNESS_STREAM`) into the run;
2. adds a first line to the brief, for example `Knowledge target: organization=acme project=acme-app`.

## Fail closed

If no target resolves, the distiller skill and `scripts/delta_marker.py` (`plan` and `write`) stop with `BLOCKER <agent>: no knowledge target resolved for ROLE/STREAM`, where STREAM is `default` when no stream was chosen. No marker is written.

## Tools

The distiller agent has Read, Grep, Glob, Write and only these pai-console tools: `knowledge_search`, `knowledge_get`, `knowledge_create`, `knowledge_update`, `knowledge_link`, `knowledge_batch`, `knowledge_audit` and `page_search`. A test pins the list.
