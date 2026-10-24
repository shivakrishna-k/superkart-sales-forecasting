#!/usr/bin/env bash
# Builds and starts the SuperKart backend (Flask, port 7860) and frontend (Streamlit, port 8501)
# as two containers connected through a Docker network. Run from the repository root.
set -e

# Remove containers/network from a previous run (ignore errors if they do not exist)
docker rm -f frontend backend 2>/dev/null || true
docker network rm superkart-network 2>/dev/null || true

# Shared network so the frontend can reach the backend at http://backend:7860
docker network create superkart-network

docker build -t superkart-backend ./backend
docker run -d --name backend --network superkart-network -p 7860:7860 superkart-backend

docker build -t superkart-frontend ./frontend
docker run -d --name frontend --network superkart-network -p 8501:8501 superkart-frontend

docker ps
echo "Backend:  port 7860 | Frontend: port 8501 (open the forwarded URLs from the Codespaces Ports tab)"
