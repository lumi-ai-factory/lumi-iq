#!/bin/bash
# ==============================================================================
# LUMI-IQ Central Application Sync Script
# Synchronizes build/staging tree (/pfs/lustrep1/appl/local/lumiiq)
# to system application tree (/appl/local/lumiiq)
#
# Project: LUMI-IQ - Work Package 2
# ==============================================================================

set -euo pipefail

# ANSI color codes
BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

SOURCE_ROOT="${SOURCE_ROOT:-/pfs/lustrep1/appl/local/lumiiq}"
TARGET_ROOT="${TARGET_ROOT:-/appl/local/lumiiq}"

# Allow local test override if running locally outside LUMI
if [ ! -d "/pfs/lustrep1" ] && [ -d "./pfs/lustrep1/appl/local/lumiiq" ]; then
    SOURCE_ROOT="./pfs/lustrep1/appl/local/lumiiq"
    TARGET_ROOT="./appl/local/lumiiq"
fi

DRY_RUN=false
SYNC_SUBDIR=""

# Parse command line flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --software-only)
            SYNC_SUBDIR="software"
            shift
            ;;
        --modules-only)
            SYNC_SUBDIR="modulefiles"
            shift
            ;;
        --scripts-only)
            SYNC_SUBDIR="scripts"
            shift
            ;;
        --source)
            SOURCE_ROOT="$2"
            shift 2
            ;;
        --target)
            TARGET_ROOT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --dry-run, -n      Perform trial run with no changes made"
            echo "  --software-only    Sync only the software/ container directory"
            echo "  --modules-only     Sync only modulefiles/"
            echo "  --scripts-only     Sync only scripts/"
            echo "  --source <PATH>    Override source root (default: /pfs/lustrep1/appl/local/lumiiq)"
            echo "  --target <PATH>    Override target root (default: /appl/local/lumiiq)"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown argument: $1${RESET}"
            exit 1
            ;;
    esac
done

echo -e "${BOLD}${CYAN}======================================================================${RESET}"
echo -e "${BOLD}${CYAN}          LUMI-IQ Central Sync (/pfs/lustrep1 -> /appl/local)          ${RESET}"
echo -e "${BOLD}${CYAN}======================================================================${RESET}"
echo -e "Source (Lustre Staging) : ${BOLD}$SOURCE_ROOT${RESET}"
echo -e "Target (System Appl)   : ${BOLD}$TARGET_ROOT${RESET}"
if [ "$DRY_RUN" = "true" ]; then
    echo -e "Mode                   : ${YELLOW}DRY RUN (Trial mode, no files modified)${RESET}"
else
    echo -e "Mode                   : ${GREEN}LIVE EXECUTION${RESET}"
fi
if [ -n "$SYNC_SUBDIR" ]; then
    echo -e "Subdirectory Filter    : ${BOLD}$SYNC_SUBDIR${RESET}"
fi
echo -e "${CYAN}----------------------------------------------------------------------${RESET}"

# 1. Validation of Source Directory
if [ ! -d "$SOURCE_ROOT" ]; then
    echo -e "${RED}[ERROR] Source directory does not exist: $SOURCE_ROOT${RESET}"
    exit 1
fi

# 2. Ensure target root directory exists or create it
if [ "$DRY_RUN" = "false" ] && [ ! -d "$TARGET_ROOT" ]; then
    echo -e "${YELLOW}[NOTICE] Creating target root: $TARGET_ROOT${RESET}"
    mkdir -p "$TARGET_ROOT"
fi

# 3. Formulate rsync command
RSYNC_FLAGS="-rlptDvh --omit-dir-times --delete"
if [ "$DRY_RUN" = "true" ]; then
    RSYNC_FLAGS="$RSYNC_FLAGS --dry-run"
fi

SRC_PATH="$SOURCE_ROOT/"
DST_PATH="$TARGET_ROOT/"

if [ -n "$SYNC_SUBDIR" ]; then
    SRC_PATH="$SOURCE_ROOT/$SYNC_SUBDIR/"
    DST_PATH="$TARGET_ROOT/$SYNC_SUBDIR/"
    if [ "$DRY_RUN" = "false" ]; then
        mkdir -p "$DST_PATH"
    fi
fi

echo -e "${BOLD}Starting rsync synchronization...${RESET}"
rsync $RSYNC_FLAGS "$SRC_PATH" "$DST_PATH" || {
    status=$?
    if [ $status -eq 23 ]; then
        echo -e "${YELLOW}[WARNING] rsync completed with attribute/timestamp warnings on shared directory (code 23). Continuing...${RESET}"
    else
        exit $status
    fi
}

# 4. Enforce strict permissions (Group + World Read/Execute)
if [ "$DRY_RUN" = "false" ]; then
    echo -e "${BOLD}Enforcing permissions (g+rX, o+rX)...${RESET}"
    chmod -R g+rX,o+rX "$TARGET_ROOT" 2>/dev/null || true

    # Attempt to set project group if available
    for grp in "lumiiq" "${LUMI_PROJECT:-}"; do
        if [ -n "$grp" ] && getent group "$grp" &>/dev/null 2>&1; then
            chgrp -R "$grp" "$TARGET_ROOT" 2>/dev/null || true
            break
        fi
    done
fi

echo -e "${BOLD}${GREEN}======================================================================${RESET}"
echo -e "${BOLD}${GREEN}[SUCCESS] LUMI-IQ synchronization completed successfully!${RESET}"
echo -e "${BOLD}${GREEN}======================================================================${RESET}"
echo -e "Verify modules via:"
echo -e "  ${CYAN}module use $TARGET_ROOT/modulefiles${RESET}"
echo -e "  ${CYAN}module avail Lumi-IQ-qaas${RESET}"
echo -e "  ${CYAN}module load Lumi-IQ-qaas/VLQ${RESET}"
echo -e "${BOLD}${GREEN}======================================================================${RESET}"
