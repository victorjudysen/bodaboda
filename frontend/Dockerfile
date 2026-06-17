FROM nginx:alpine

# Copy startup script before the nginx entrypoint runs.
# ENTRYPOINT overrides the official nginx entrypoint entirely, so
# there is no conflict with /docker-entrypoint.sh template processing.
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Template is processed by start.sh using sed (always available in alpine).
COPY nginx.conf.template /etc/nginx/nginx.conf.template

COPY index.html login.html register.html request.html dashboard.html rider-dashboard.html \
     /usr/share/nginx/html/
COPY css/ /usr/share/nginx/html/css/
COPY js/  /usr/share/nginx/html/js/

# Default for local Docker Compose; overridden on Render via env var.
ENV BACKEND_URL=http://backend:5000

EXPOSE 80

# Use ENTRYPOINT (not CMD) so this script is always the process run,
# never passed as an argument to the nginx entrypoint.
ENTRYPOINT ["/start.sh"]
