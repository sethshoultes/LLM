#!/bin/bash
# llm_rag.sh - Run the LLM interface with RAG support

# Define color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "${BLUE}Starting LLM interface with RAG support${NC}"

# Activate the virtual environment
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Mac OS
    ACTIVATE_SCRIPT="$DIR/LLM-MODELS/tools/scripts/activate_mac.sh"
elif [[ "$OSTYPE" == "linux"* ]]; then
    # Linux (Raspberry Pi)
    ACTIVATE_SCRIPT="$DIR/LLM-MODELS/tools/scripts/activate_pi.sh"
fi

# Source the activation script if it exists
if [ -f "$ACTIVATE_SCRIPT" ]; then
    source "$ACTIVATE_SCRIPT"
    echo -e "${GREEN}Activated Python environment${NC}"
else
    echo -e "${YELLOW}Warning: Could not find virtual environment activation script.${NC}"
    echo -e "${YELLOW}Some features may not work correctly.${NC}"
fi

# Check if the RAG module exists
if [ ! -d "$DIR/rag_support" ]; then
    echo -e "${RED}Error: RAG support module not found.${NC}"
    exit 1
fi

# Run the enhanced interface
python "$DIR/scripts/quiet_interface_rag.py"