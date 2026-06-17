FROM nginx:alpine

# Use a custom startup script so BACKEND_URL always gets a safe default
# even when the container platform (e.g. Render) injects an empty string.
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Template is processed by start.sh at runtime, not by the nginx entrypoint.
COPY nginx.conf.template /etc/nginx/nginx.conf.template

COPY index.html login.html register.html request.html dashboard.html rider-dashboard.html \
     /usr/share/nginx/html/
COPY css/ /usr/share/nginx/html/css/
COPY js/  /usr/share/nginx/html/js/

# Default for local Docker Compose; overridden by BACKEND_URL env var on Render.
ENV BACKEND_URL=http://backend:5000

EXPOSE 80

CMD ["/start.sh"]
