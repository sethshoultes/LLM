#!/bin/bash
# Clear all caches for the LLM platform

# Ensure we're in the base directory
cd "$(dirname "$0")"

# Source the activation script to ensure the environment is active
if [ -f "LLM-MODELS/tools/scripts/activate_mac.sh" ]; then
    echo "Activating environment..."
    source LLM-MODELS/tools/scripts/activate_mac.sh
fi

# Clear all caches
echo "Clearing all caches..."
python3 scripts/clear_caches.py --all

echo ""
echo "To restart the system with a clean slate, run:"
echo "./llm.sh --rag"