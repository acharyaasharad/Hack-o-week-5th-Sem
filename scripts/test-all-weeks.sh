#!/bin/bash
# Test All Weeks in Hack-o-Week
set -e

echo "=========================================="
echo " Running All Hack-o-Week Test Suites      "
echo "=========================================="

FAILED_WEEKS=()

run_suite() {
    local week_dir=$1
    local name=$2
    echo ""
    echo "▶ Testing $name ($week_dir)..."
    if [ -d "$week_dir/tests" ]; then
        if PYTHONPATH="$week_dir" python3 -m pytest "$week_dir/tests" -q; then
            echo "✅ $name tests passed."
        else
            echo "❌ $name tests failed."
            FAILED_WEEKS+=("$name")
        fi
    else
        echo "ℹ️ No tests directory in $week_dir."
    fi
}

run_suite "W3-4" "W3-4 MovieScope Analytics"
run_suite "W5-6" "W5-6 Touchline Analytics"
run_suite "W7-8" "W7-8 Energy Intelligence & Optimization"
run_suite "W9-10" "W9-10 Customer Segmentation Studio"
run_suite "W11-12" "W11-12 PCA & t-SNE Studio"
run_suite "W13-14" "W13-14 Ensemble Learning & Generalization Lab"
echo ""
echo "▶ Testing W14-15 Activation Function Visualizer (W14-15)..."
if (cd W14-15 && python3 -m unittest test_activation_functions.py -v); then
    echo "✅ W14-15 Activation Function Visualizer tests passed."
else
    echo "❌ W14-15 Activation Function Visualizer tests failed."
    FAILED_WEEKS+=("W14-15")
fi

echo ""
echo "=========================================="
if [ ${#FAILED_WEEKS[@]} -eq 0 ]; then
    echo "🎉 All test suites passed successfully!"
    exit 0
else
    echo "❌ Some test suites failed: ${FAILED_WEEKS[*]}"
    exit 1
fi
