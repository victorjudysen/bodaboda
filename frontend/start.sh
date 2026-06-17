#!/bin/sh
# Ensure BACKEND_URL always has a value before nginx processes the config.
# Render sets it to empty string when left blank; this catches that case.
BACKEND_URL="${BACKEND_URL:-http://backend:5000}"
export BACKEND_URL

envsubst '${BACKEND_URL}' \
  < /etc/nginx/nginx.conf.template \
  > /etc/nginx/conf.d/default.conf

echo "Starting nginx with BACKEND_URL=${BACKEND_URL}"
exec nginx -g 'daemon off;'
