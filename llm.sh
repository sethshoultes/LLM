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

# Initialize flags
RAG_ENABLED=0
DEBUG_MODE=0
RAG_SMART_CONTEXT=1  # Enable smart context by default
COMMAND="start"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --rag)
            RAG_ENABLED=1
            shift
            ;;
        --debug)
            DEBUG_MODE=1
            shift
            ;;
        --no-smart-context)
            RAG_SMART_CONTEXT=0
            shift
            ;;
        --help|-h)
            COMMAND="help"
            shift
            ;;
        download|samples)
            COMMAND="$1"
            shift
            ;;
        *)
            # If it doesn't start with -- or isn't a known command, treat as unrecognized
            if [[ "$1" == --* ]]; then
                echo -e "${RED}Unrecognized option: $1${NC}"
                COMMAND="help"
            else
                echo -e "${RED}Unrecognized command: $1${NC}"
                COMMAND="help"
            fi
            shift
            ;;
    esac
done

# Set environment variables
export LLM_BASE_DIR="$DIR"
export LLM_RAG_ENABLED="$RAG_ENABLED"
export LLM_DEBUG_MODE="$DEBUG_MODE"
export LLM_RAG_SMART_CONTEXT="$RAG_SMART_CONTEXT"
export PYTHONPATH="$DIR:$PYTHONPATH"

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
    echo -e "Usage: ./llm.sh [options]"
    echo ""
    echo -e "Options:"
    echo -e "  ${GREEN}--rag${NC}              Enable RAG (Retrieval Augmented Generation) features"
    echo -e "  ${GREEN}--debug${NC}            Enable debug mode (shows additional output)"
    echo -e "  ${GREEN}--no-smart-context${NC} Disable smart context management for RAG (on by default)"
    echo -e "  ${GREEN}--help, -h${NC}         Show this help message"
    echo ""
    echo -e "Commands:"
    echo -e "  ${GREEN}download${NC}       Download a model from HuggingFace"
    echo -e "  ${GREEN}samples${NC}        Download sample models for testing"
    echo ""
    echo -e "Examples:"
    echo -e "  ${BLUE}./llm.sh${NC}                                 - Start the standard interface"
    echo -e "  ${BLUE}./llm.sh --rag${NC}                           - Start with RAG features enabled"
    echo -e "  ${BLUE}./llm.sh --rag --no-smart-context${NC}        - Start RAG without smart context"
    echo -e "  ${BLUE}./llm.sh --debug${NC}                         - Start with debug mode enabled"
    echo -e "  ${BLUE}./llm.sh --rag --debug${NC}                   - Start with both RAG and debug enabled"
    echo -e "  ${BLUE}./llm.sh download${NC}                        - Download models"
    echo ""
    echo -e "Documentation:"
    echo -e "  See the ${BLUE}docs/${NC} directory for detailed documentation"
    echo -e "  - ${BLUE}docs/USAGE.md${NC}                 - User guide"
    echo -e "  - ${BLUE}docs/MODELS.md${NC}                - Model information"
    echo -e "  - ${BLUE}docs/RAG_USAGE.md${NC}             - RAG usage guide"
    echo -e "  - ${BLUE}docs/DEVELOPMENT.md${NC}           - Developer documentation"
    echo ""
}

# Execute the requested command
case "$COMMAND" in
    "start")
        print_banner
        echo -e "Starting LLM interface..."
        
        # Show enabled features
        FEATURES=""
        if [ "$RAG_ENABLED" == "1" ]; then
            FEATURES="${FEATURES}RAG "
            echo -e "- RAG features are ${GREEN}enabled${NC}"
            
            # Show smart context status if RAG is enabled
            if [ "$RAG_SMART_CONTEXT" == "1" ]; then
                echo -e "  - Smart Context is ${GREEN}enabled${NC}"
            else
                echo -e "  - Smart Context is ${YELLOW}disabled${NC}"
            fi
        fi
        if [ "$DEBUG_MODE" == "1" ]; then
            FEATURES="${FEATURES}Debug "
            echo -e "- Debug mode is ${GREEN}enabled${NC}"
        fi
        
        if [ -n "$FEATURES" ]; then
            echo -e "Starting with ${GREEN}${FEATURES}${NC}features enabled."
        fi
        
        # Launch the interface
        python3 "$DIR/scripts/quiet_interface.py"
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
        echo -e "${RED}Unknown command!${NC}"
        print_help
        exit 1
        ;;
esac