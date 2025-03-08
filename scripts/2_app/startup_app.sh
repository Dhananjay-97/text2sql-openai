#!/bin/bash
set -eox pipefail

cleanup() {
    # kill all processes whose parent is this process
    pkill -P $$
}

for sig in INT QUIT HUP TERM; do
  trap "
    cleanup
    trap - $sig EXIT
    kill -s $sig "'"$$"' "$sig"
done
trap cleanup EXIT

export RAG_DATABASES_DIR=$(pwd)/databases
export API_URL="http://localhost:8080"

# Start FastAPI backend
uvicorn backend:app --reload --host 0.0.0.0 --port 8080 > backend.log 2>&1 &

# Start Streamlit frontend
streamlit run frontend.py > frontend.log 2>&1 &

while ! curl --output /dev/null --silent --fail http://localhost:8080/docs; do
    echo "Waiting for the Python backend to be ready..."
    sleep 4
done
