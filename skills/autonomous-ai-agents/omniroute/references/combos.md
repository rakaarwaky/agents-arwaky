# Combo routing

The reason to use OmniRoute over a plain provider list — combos pick a model by task shape
instead of you naming one:

```bash
curl $OMNIROUTE_URL/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"auto/best-free","messages":[{"role":"user","content":"hi"}]}'
```

| Combo | Use for |
|-------|---------|
| `auto/best-free` | only free tiers — cheapest and safest |
| `auto/best-coding` | coding tasks |
| `auto/best-fast` | low-latency replies |
| `auto/best-chat` | general conversation |
