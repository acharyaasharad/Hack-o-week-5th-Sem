#!/bin/bash
# Stop all weekly applications running on ports 3000, 5001-5006
PORTS=(3000 5001 5002 5003 5004 5005 5006)

echo "Stopping all Hack-o-Week applications..."

for port in "${PORTS[@]}"; do
    pids=$(lsof -ti :"$port")
    if [ -n "$pids" ]; then
        echo "Killing processes on port $port (PIDs: $pids)..."
        kill -9 $pids 2>/dev/null || true
    else
        echo "Port $port: No active process."
    fi
done

echo "Done."
