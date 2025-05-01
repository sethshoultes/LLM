#!/bin/bash

# Navigate to the tests directory
cd "$(dirname "$0")"

# Source the activation script (adjust path as needed)
source ../LLM-MODELS/tools/scripts/activate_mac.sh

# Create test directories if they don't exist
mkdir -p test_data
mkdir -p test_data/projects

# Run the RAG tests
echo -e "\n=== Running RAG system tests ==="
python3 test_rag.py
RAG_EXIT_CODE=$?

# Run the Project Manager tests
echo -e "\n=== Running Project Manager tests ==="
python3 test_project_manager.py
PM_EXIT_CODE=$?

# Run the Integration tests
echo -e "\n=== Running RAG Integration tests ==="
python3 test_rag_integration.py
INTEGRATION_EXIT_CODE=$?

# Calculate overall exit code
if [ $RAG_EXIT_CODE -eq 0 ] && [ $PM_EXIT_CODE -eq 0 ] && [ $INTEGRATION_EXIT_CODE -eq 0 ]; then
    EXIT_CODE=0
else
    EXIT_CODE=1
fi

# Print summary
echo -e "\n=== Test Summary ==="
echo "RAG System Tests: $([ $RAG_EXIT_CODE -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
echo "Project Manager Tests: $([ $PM_EXIT_CODE -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
echo "Integration Tests: $([ $INTEGRATION_EXIT_CODE -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
echo "-------------------"

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n✅ All tests passed!"
else
    echo -e "\n❌ Some tests failed!"
fi

# Return the exit code
exit $EXIT_CODE