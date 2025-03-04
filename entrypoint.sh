#!/bin/bash
set -eox pipefail

# Load environment variables from a .env file (optional, for local dev)
#if [ -f .env ]; then
#  source .env
#fi

mkdir -p sessions index images

uvicorn scripts/2_app/backend:app --reload --host 0.0.0.0 --port 8080 > backend.log 2>&1 &

streamlit run scripts/2_app/frontend.py --server.port 8501 --server.address 0.0.0.0 2>&1 > frontend.log &

sleep 10

wait
