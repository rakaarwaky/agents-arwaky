# Errors

- Port already bound → something else holds 7777; check `ss -ltn | grep 7777`, then change
  `PORT` in `~/.omniroute/.env` and `aa omniroute restart`
- Configs unreadable after an upgrade → `STORAGE_ENCRYPTION_KEY` changed; restore the
  previous `~/.omniroute/.env`. Check `omniroute doctor`
- `omniroute serve` exits immediately → run `omniroute doctor`; the port is the usual cause
