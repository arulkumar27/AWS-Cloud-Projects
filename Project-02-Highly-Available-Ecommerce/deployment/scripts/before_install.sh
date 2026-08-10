#!/usr/bin/env bash
set -euo pipefail
systemctl stop ecommerce.service 2>/dev/null || true
find /opt/ecommerce-app -mindepth 1 -maxdepth 1 -exec rm -rf {} +
