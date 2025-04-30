#!/bin/bash

# Navigate to the tests directory
cd "$(dirname "$0")"

# Source the activation script (adjust path as needed)
source ../LLM-MODELS/tools/scripts/activate_mac.sh

# Create test directories if they don't exist
mkdir -p test_data

# Run the RAG tests
echo "Running RAG system tests..."
python3 test_rag.py

# Save the exit code
EXIT_CODE=$?

# Print summary
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n✅ All tests passed!"
else
    echo -e "\n❌ Some tests failed!"
fi

# Return the exit code
exit $EXIT_CODE