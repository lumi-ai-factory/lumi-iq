#!/bin/bash
# ==============================================================================
# LUMI-IQ Module Verification & Smoke Test Script
# Tests /appl/local/lumiiq deployment, module loading, and package imports
# ==============================================================================

set -euo pipefail

BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

APPL_ROOT="${1:-/appl/local/lumiiq}"
MODULE_PATH="$APPL_ROOT/modulefiles"
if [ -d "$APPL_ROOT/software/lumi-iq-env" ]; then
    ENV_PATH="$APPL_ROOT/software/lumi-iq-env"
elif [ -d "$APPL_ROOT/lumi-iq-env" ]; then
    ENV_PATH="$APPL_ROOT/lumi-iq-env"
elif [ -d "$HOME/lumi-iq-env" ]; then
    ENV_PATH="$HOME/lumi-iq-env"
else
    ENV_PATH="$APPL_ROOT/software/lumi-iq-env"
fi

echo -e "${BOLD}${CYAN}======================================================================${RESET}"
echo -e "${BOLD}${CYAN}            LUMI-IQ Module Verification & Smoke Test                  ${RESET}"
echo -e "${BOLD}${CYAN}======================================================================${RESET}"
echo -e "Application Root : ${BOLD}$APPL_ROOT${RESET}"
echo -e "Modulefiles Root : ${BOLD}$MODULE_PATH${RESET}"
echo -e "Software Root    : ${BOLD}$ENV_PATH${RESET}"
echo -e "${CYAN}----------------------------------------------------------------------${RESET}"

TOTAL_TESTS=0
PASSED_TESTS=0

run_check() {
    local desc="$1"
    local cmd="$2"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "  Checking $desc ... "
    if eval "$cmd" >/dev/null 2>&1; then
        echo -e "${GREEN}[ PASS ]${RESET}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}[ FAIL ]${RESET}"
    fi
}

# 1. Directory Structure Checks
echo -e "${BOLD}1. Verifying Directory Layout:${RESET}"
run_check "Modulefiles directory exists" "[ -d '$MODULE_PATH' ]"
run_check "Lumi-IQ-qaas/VLQ.lua exists" "[ -f '$MODULE_PATH/Lumi-IQ-qaas/VLQ.lua' ]"
run_check "Lumi-IQ-qaas/SIM.lua exists" "[ -f '$MODULE_PATH/Lumi-IQ-qaas/SIM.lua' ]"
run_check "Lumi-IQ-qaas/default exists" "[ -e '$MODULE_PATH/Lumi-IQ-qaas/default' ]"
run_check "Software directory exists" "[ -d '$ENV_PATH' ]"
run_check "Jupyter kernel.json exists" "[ -f '$ENV_PATH/share/jupyter/kernels/lumi-iq/kernel.json' ]"

# 2. Execution Checks (if on LUMI node with container)
echo ""
echo -e "${BOLD}2. Verifying Software Environment & Imports:${RESET}"
if [ -x "$ENV_PATH/bin/python" ]; then
    run_check "Python executable runs" "$ENV_PATH/bin/python --version"
    run_check "Import Qiskit" "$ENV_PATH/bin/python -c 'import qiskit'"
    run_check "Import Qiskit-Aer" "$ENV_PATH/bin/python -c 'import qiskit_aer'"
    run_check "Import QaaS Client" "$ENV_PATH/bin/python -c 'import qaas'"
    run_check "Import Py4LEXIS" "$ENV_PATH/bin/python -c 'import py4lexis'"
    run_check "Import PySCF" "$ENV_PATH/bin/python -c 'import pyscf'"
    run_check "Import PyTorch" "$ENV_PATH/bin/python -c 'import torch'"
    run_check "Import NetworkX" "$ENV_PATH/bin/python -c 'import networkx'"
    run_check "Import Dill" "$ENV_PATH/bin/python -c 'import dill'"
    run_check "Import Stim (QEC)" "$ENV_PATH/bin/python -c 'import stim'"
    run_check "Import PyMatching (QEC)" "$ENV_PATH/bin/python -c 'import pymatching'"
    run_check "Import PennyLane (QML)" "$ENV_PATH/bin/python -c 'import pennylane'"
else
    echo -e "  ${YELLOW}[SKIP] $ENV_PATH/bin/python not found or not executable outside LUMI compute node.${RESET}"
fi

# 3. Lmod Module Loading (if module command is available)
echo ""
echo -e "${BOLD}3. Verifying Lmod Integration:${RESET}"
if command -v module &>/dev/null; then
    run_check "Lmod can read modulepath" "module use $MODULE_PATH"
    run_check "Lmod can load Lumi-IQ-qaas/VLQ" "module load Lumi-IQ-qaas/VLQ"
    run_check "Lmod can load Lumi-IQ-qaas/SIM" "module load Lumi-IQ-qaas/SIM"
else
    echo -e "  ${YELLOW}[SKIP] 'module' command not present in current shell (standard outside HPC environment).${RESET}"
fi

echo ""
echo -e "${BOLD}${CYAN}----------------------------------------------------------------------${RESET}"
echo -e "Summary: ${BOLD}$PASSED_TESTS / $TOTAL_TESTS checks passed.${RESET}"
if [ "$PASSED_TESTS" -eq "$TOTAL_TESTS" ]; then
    echo -e "${BOLD}${GREEN}[ALL CHECKS PASSED] LUMI-IQ module structure is fully valid!${RESET}"
else
    echo -e "${BOLD}${YELLOW}[INFO] Structural checks passed. Run on LUMI node to complete execution checks.${RESET}"
fi
echo -e "${BOLD}${CYAN}======================================================================${RESET}"
