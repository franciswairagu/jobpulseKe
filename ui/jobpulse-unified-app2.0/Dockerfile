# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files (build context is repo root)
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

# Copy nginx config template (envsubst will fill ${PORT} and ${BACKEND_URL} at startup)
COPY ui/jobpulse-unified-app2.0/nginx.conf /etc/nginx/templates/default.conf.template

# Defaults — override via Railway env vars PORT and BACKEND_URL
ENV PORT=80
ENV BACKEND_URL=http://localhost:8000

# Copy built files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# Health check uses the dynamic PORT
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:${PORT}/ || exit 1

CMD ["/bin/sh", "-c", "export PORT=${PORT:-80} && export BACKEND_URL=${BACKEND_URL:-http://localhost:8000} && envsubst '${PORT} ${BACKEND_URL}' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
