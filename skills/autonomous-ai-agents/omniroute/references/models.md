# Models

```bash
curl $OMNIROUTE_URL/v1/models          # everything currently routable
omniroute models --free                # free tiers only, via the CLI
```

To **rank or tier** the models returned by `/v1/models` into a capability
table (a model inventory / tier list), follow
[`references/model-tier-list.md`](references/model-tier-list.md).

The concrete `GET /v1/models` response shape and dedupe suffix list are in
[`references/omniroute-models-shape.md`](references/omniroute-models-shape.md).
