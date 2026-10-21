#!/bin/bash
# Hack-o-Week Orchestrator: Start and Verify All Weekly Web Applications
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                  HACK-O-WEEK: ALL WEEKS RUNNER                           ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""

is_port_listening() {
    lsof -i :"$1" -sTCP:LISTEN >/dev/null 2>&1
}

start_week() {
    local week_dir=$1
    local port=$2
    local start_cmd=$3
    local name=$4

    if is_port_listening "$port"; then
        echo "✅ [$port] $name is already running."
    else
        echo "🚀 [$port] Starting $name..."
        (cd "$ROOT_DIR/$week_dir" && nohup $start_cmd > "server.log" 2>&1 &)
        sleep 1.5
        if is_port_listening "$port"; then
            echo "✅ [$port] $name started successfully."
        else
            echo "⚠️ [$port] $name did not respond immediately. Check $week_dir/server.log."
        fi
    fi
}

start_week "W1-2" 3000 "npm start" "W1-2: Expense Tracker REST API"
start_week "W3-4" 5001 "python3 app.py" "W3-4: MovieScope Analytics Studio"
start_week "W5-6" 5002 "python3 app.py" "W5-6: Touchline Football Analytics"
start_week "W7-8" 5003 "python3 app.py" "W7-8: Energy Intelligence & Optimization"
start_week "W9-10" 5004 "python3 app.py" "W9-10: Customer Segmentation Dashboard"
start_week "W11-12" 5005 "python3 app.py" "W11-12: PCA & t-SNE Studio"
start_week "W13-14" 5006 "python3 app.py" "W13-14: Ensemble Learning & Generalization Lab"

echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo " Weekly Application Status & URLs:"
echo "════════════════════════════════════════════════════════════════════════════"
for port in 3000 5001 5002 5003 5004 5005 5006; do
    if is_port_listening "$port"; then
        code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$port/")
        echo "  • Port $port: http://127.0.0.1:$port (HTTP $code)"
    else
        echo "  • Port $port: OFFLINE"
    fi
done
echo "════════════════════════════════════════════════════════════════════════════"
