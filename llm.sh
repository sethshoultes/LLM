#!/bin/bash
# llm.sh - Main entry point for the Portable LLM Environment
# Provides a unified interface to all functionality

# Set color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

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

# Banner
print_banner() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}                 Portable LLM Environment                      ${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

# Help message
print_help() {
    echo -e "Usage: ./llm.sh [command]"
    echo ""
    echo -e "Commands:"
    echo -e "  ${GREEN}quiet${NC}        - Start the recommended interface (suppresses debug output)"
    echo -e "  ${GREEN}start${NC}        - Same as quiet"
    echo -e "  ${GREEN}download${NC}     - Download a model from HuggingFace"
    echo -e "  ${GREEN}samples${NC}      - Download sample models for testing"
    echo -e "  ${GREEN}help${NC}         - Show this help message"
    echo ""
    echo -e "Legacy Commands (all redirect to quiet interface):"
    echo -e "  ${YELLOW}flask${NC}, ${YELLOW}simple${NC}, ${YELLOW}minimal${NC}"
    echo ""
    echo -e "Documentation:"
    echo -e "  See the ${BLUE}docs/${NC} directory for detailed documentation"
    echo -e "  - ${BLUE}docs/USAGE.md${NC}        - User guide"
    echo -e "  - ${BLUE}docs/MODELS.md${NC}       - Model information"
    echo -e "  - ${BLUE}docs/DEVELOPMENT.md${NC}  - Developer documentation"
    echo ""
}

# Parse command
COMMAND=${1:-start}

# Execute the requested command
case "$COMMAND" in
    "start")
        print_banner
        echo -e "Starting default LLM interface..."
        echo -e "NOTE: If this fails, try one of the alternative launchers:"
        echo -e "  ./llm.sh quiet   - Recommended quiet interface"
        echo -e "  ./llm.sh simple  - Simple HTTP server interface"
        echo -e "  ./llm.sh minimal - Minimal interface with no dependencies"
        PYTHONPATH="$DIR/scripts" python3 "$DIR/scripts/quiet_interface.py"
        ;;
    "quiet")
        print_banner
        echo -e "Starting quiet LLM interface..."
        echo -e "This interface suppresses debug output for a cleaner experience."
        PYTHONPATH="$DIR/scripts" python3 "$DIR/scripts/quiet_interface.py"
        ;;
    "flask"|"simple"|"minimal")
        print_banner
        echo -e "Starting LLM interface..."
        echo -e "${YELLOW}Note: All interface options now use the quiet interface, which combines the best features.${NC}"
        PYTHONPATH="$DIR/scripts" python3 "$DIR/scripts/quiet_interface.py"
        ;;
    "download")
        print_banner
        echo -e "Starting model download..."
        bash "$DIR/scripts/direct_download.sh"
        ;;
    "samples")
        print_banner
        echo -e "Downloading sample models for testing..."
        bash "$DIR/scripts/download_sample_models.sh"
        ;;
    "help")
        print_banner
        print_help
        ;;
    *)
        print_banner
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        print_help
        exit 1
        ;;
esac