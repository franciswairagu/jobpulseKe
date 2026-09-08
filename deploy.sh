#!/bin/bash
set -e

echo "=========================================="
echo "   JobPulse Docker Deployment"
echo "=========================================="
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed."
    echo "Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "[ERROR] Docker Compose is not installed."
    echo "Install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Create .env if not exists
if [ ! -f .env ]; then
    echo "[1/4] Creating .env file..."
    SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
    cat > .env << EOF
DATABASE_URL=sqlite:///./jobpulse.db
SECRET_KEY=$SECRET_KEY
CORS_ORIGINS=["http://localhost","http://localhost:80"]
ENVIRONMENT=production
EOF
    echo "      .env created with random SECRET_KEY"
else
    echo "[1/4] .env file already exists"
fi

# Stop existing containers
echo "[2/4] Stopping existing containers..."
docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true

# Build and start
echo "[3/4] Building and starting services..."
docker-compose up -d --build 2>/dev/null || docker compose up -d --build

# Wait for services to be healthy
echo "[4/4] Waiting for services to start..."
sleep 10

# Check status
echo ""
echo "=========================================="
echo "   Deployment Status"
echo "=========================================="
echo ""

if docker-compose ps 2>/dev/null | grep -q "backend.*Up\|healthy" || docker compose ps 2>/dev/null | grep -q "backend.*Up\|healthy"; then
    echo "[OK] Backend is running  -> http://localhost:8000"
    echo "[OK] API Docs           -> http://localhost:8000/docs"
else
    echo "[WARN] Backend may not be ready yet"
fi

if docker-compose ps 2>/dev/null | grep -q "frontend.*Up\|healthy" || docker compose ps 2>/dev/null | grep -q "frontend.*Up\|healthy"; then
    echo "[OK] Frontend is running -> http://localhost:80"
else
    echo "[WARN] Frontend may not be ready yet"
fi

echo ""
echo "=========================================="
echo "   Useful Commands"
echo "=========================================="
echo ""
echo "  View logs:        docker-compose logs -f"
echo "  Stop services:    docker-compose down"
echo "  Restart:          docker-compose restart"
echo "  Rebuild:          docker-compose up -d --build"
echo "  Check status:     docker-compose ps"
echo ""
echo "=========================================="
