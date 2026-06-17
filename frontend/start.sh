#!/bin/sh
set -e

# Always fall back to the Docker Compose internal hostname if BACKEND_URL
# is empty (Render sets it to empty string when left blank).
BACKEND_URL="${BACKEND_URL:-http://backend:5000}"
export BACKEND_URL

echo "[BodaBoda] BACKEND_URL=${BACKEND_URL}"

# Use sed — guaranteed available in nginx:alpine (busybox).
# Replaces the literal token BACKEND_URL_PLACEHOLDER with the real value.
sed "s|BACKEND_URL_PLACEHOLDER|${BACKEND_URL}|g" \
  /etc/nginx/nginx.conf.template \
  > /etc/nginx/conf.d/default.conf

echo "[BodaBoda] nginx config written — starting nginx"
exec nginx -g 'daemon off;'
