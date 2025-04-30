#!/bin/bash

# Navigate to the LLM directory
cd "$(dirname "$0")"

# Source the activation script
source LLM-MODELS/tools/scripts/activate_mac.sh

# Install dependencies
pip install -r config/requirements.txt

# Test RAG import
echo "Testing RAG module import..."
python3 -c "import rag; print(f'RAG module version: {rag.__version__}'); print('Successfully imported components:'); print(rag.__all__)"

echo "RAG setup complete."