# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY ui/jobpulse-unified-app2.0/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY ui/jobpulse-unified-app2.0/ .

# Build for production
RUN npm run build

# Production stage
FROM nginx:alpine

# Install envsubst (from gettext)
RUN apk add --no-cache gettext

# Copy nginx config OUTSIDE of /etc/nginx/templates/ to avoid the
# entrypoint's envsubst which replaces ALL env vars (breaking $host, $remote_addr, etc.)
COPY ui/jobpulse-unified-app2.0/nginx.conf /etc/nginx/app.conf.template

# Set default backend URL for docker-compose compatibility
ENV BACKEND_URL=http://backend:8000

# Copy built files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/ || exit 1

CMD ["/bin/sh", "-c", "envsubst '${BACKEND_URL}' < /etc/nginx/app.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
