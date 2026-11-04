# GIF Search — Setup

## Prerequisites

- `curl` and `jq` (both standard on macOS/Linux)
- `TENOR_API_KEY` environment variable

## API key

Set your Tenor API key in your environment (add to `${HERMES_HOME:-~/.hermes}/.env`):

```bash
TENOR_API_KEY=your_key_here
```

Get a free API key at https://developers.google.com/tenor/guides/quickstart — the Google Cloud Console Tenor API key is free and has generous rate limits.

## Completion

- `echo $TENOR_API_KEY` is non-empty and `curl`/`jq` resolve on PATH.
