#!/bin/bash

# Simple script to start both backend and frontend development servers.
# Run this script from the root of the linkedin_project directory.

# --- Prerequisites ---
# Make sure you have:
# 1. Created the Python virtual environment in ./backend/venv
#    (Example: cd backend && python -m venv venv && cd ..)
# 2. Activated the virtual environment *before* running this script:
#    (Example: source backend/venv/bin/activate  # or backend\\venv\\Scripts\\activate on Windows)
# 3. Installed backend dependencies:
#    (Example: pip install -r backend/requirements.txt)
# 4. Installed frontend dependencies:
#    (Example: cd frontend && npm install && cd ..)
# 5. Created and configured the ./backend/.env file:
#    (Example: cp backend/.env.example backend/.env # Then edit .env)
# ---------------------

# Check if backend venv activated (basic check - checks if flask is found)
if ! command -v flask &> /dev/null
then
    echo "Flask command not found. Did you activate the backend virtual environment (source backend/venv/bin/activate)?"
    exit 1
fi

# Check if backend .env file exists
if [ ! -f backend/.env ]; then
    echo "Error: backend/.env file not found. Please create it from backend/.env.example and add your keys."
    exit 1
fi


echo "Starting backend server (Flask on port 5001)..."
cd backend
# Explicitly point to the 'app' module (app.py)
flask --app app run --port 5001 &
BACKEND_PID=$!
cd ..

# Function to kill backend server on script exit (Ctrl+C, etc.)
# Added 2>/dev/null to suppress "kill: No such process" if already stopped
trap "echo 'Stopping backend server (PID $BACKEND_PID)...'; kill $BACKEND_PID 2>/dev/null; exit" SIGINT SIGTERM EXIT

# Give backend a moment to start
sleep 2

echo "-------------------------------------------------"
echo "Starting frontend server (React + Vite)..."
echo "Access frontend at the URL provided below (usually http://localhost:5173)"
echo "Press Ctrl+C here to stop both servers."
echo "-------------------------------------------------"

cd frontend
npm run dev # This runs in the foreground

# The trap defined above will handle cleanup when npm run dev exits (e.g., via Ctrl+C)

echo "Frontend server stopped."
# Trap ensures backend is stopped too.
