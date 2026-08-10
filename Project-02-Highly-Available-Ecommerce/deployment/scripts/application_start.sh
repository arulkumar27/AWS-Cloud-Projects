#!/usr/bin/env bash
set -euo pipefail
systemctl enable --now ecommerce.service
systemctl enable --now nginx
