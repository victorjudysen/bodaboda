FROM nginx:alpine

# The official nginx:alpine image processes files under /etc/nginx/templates/
# with envsubst at startup, writing results to /etc/nginx/conf.d/.
# This lets BACKEND_URL be injected at runtime for both local Docker Compose
# and cloud deployments (Render.com).
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

COPY index.html login.html register.html request.html dashboard.html rider-dashboard.html /usr/share/nginx/html/
COPY css/ /usr/share/nginx/html/css/
COPY js/  /usr/share/nginx/html/js/

# Default points to Docker Compose internal hostname; overridden on Render.
ENV BACKEND_URL=http://backend:5000

EXPOSE 80
