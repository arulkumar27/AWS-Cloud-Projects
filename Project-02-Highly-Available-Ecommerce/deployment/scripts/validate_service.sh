#!/usr/bin/env bash
set -euo pipefail
for attempt in {1..20}; do
  if curl --fail --silent http://127.0.0.1/health >/dev/null; then
    exit 0
  fi
  sleep 3
done
journalctl -u ecommerce.service --no-pager -n 50
exit 1
