#!/usr/bin/env bash
# Render Build Script — builds both frontend and backend in one go.
set -e

echo "=== Installing & building frontend ==="
cd frontend
npm install
VITE_API_URL="" npm run build
echo "Frontend build complete → frontend/dist/"

echo "=== Installing backend dependencies ==="
cd ../backend
pip install -r requirements.txt
echo "Backend dependencies installed."

echo "=== Build finished ==="
