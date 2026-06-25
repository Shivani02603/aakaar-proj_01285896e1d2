#!/bin/bash
set -euo pipefail

# Start the backend in the background
(cd backend && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000) &

# Start the frontend development server
(cd frontend && npm run dev) &

# Wait for all background processes
wait