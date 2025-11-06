#!/bin/bash

# Minerva Full Stack Startup Script
# This script starts all required services for the Minerva application

echo "🚀 Starting Minerva Full Stack..."

# Function to start a service in background
start_service() {
    local name=$1
    local command=$2
    local working_dir=$3
    local args=$4
    
    echo "Starting $name..."
    if [ -n "$working_dir" ]; then
        cd "$working_dir"
    fi
    
    if [ -n "$args" ]; then
        $command $args &
    else
        $command &
    fi
    
    # Return to original directory
    if [ -n "$working_dir" ]; then
        cd - > /dev/null
    fi
}

# Start Temporal Server
start_service "Temporal Server" "temporal" "" "server start-dev"

# Wait a moment for Temporal to start
sleep 3

# Start Ollama Server
start_service "Ollama Server" "ollama" "" "serve"

# Wait a moment for Ollama to start
sleep 3

# Start Backend API
start_service "Backend API" "uvicorn" "backend" "src.minerva_backend.api.main:backend_app --host 0.0.0.0 --port 8000 --reload --log-level debug"

# Start Temporal Worker
start_service "Temporal Worker" "python" "backend" "src/minerva_backend/processing/temporal_orchestrator.py"

# Start Frontend
start_service "Frontend Dev Server" "npm" "frontend" "run dev"

# Open Minerva log in VS Code (if available)
if command -v code &> /dev/null; then
    echo "Opening Minerva log..."
    code backend/logs/minerva.log &
fi

echo "✅ All Minerva services started!"
echo "Services running:"
echo "  • Temporal Server: http://localhost:7233"
echo "  • Ollama Server: http://localhost:11434"
echo "  • Backend API: http://localhost:8000"
echo "  • Frontend: http://localhost:5173"
echo "  • Minerva Log: backend/logs/minerva.log"
