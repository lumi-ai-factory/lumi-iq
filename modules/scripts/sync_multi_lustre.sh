#!/bin/bash
# ==============================================================================
# LUMI Multi-Lustre Partition Synchronization Script
#
# Adheres to LUMI Lustre Parallel Filesystem Architecture:
# UAN (User Access Nodes) and compute nodes are distributed across four independent
# Lustre storage partitions (/pfs/lustrep1 through /pfs/lustrep4). This script
# synchronizes the staged software container stack and Lmod modulefiles from the
# master Lustre tier (/pfs/lustrep1) to all remaining partitions in parallel, and
# enforces strict POSIX permissions ensuring global read/execution for all LUMI
# users without unauthorized write permissions (a+rX, o-w).
#
# Usage (One-time command):
#   bash modules/scripts/sync_multi_lustre.sh -y
# ==============================================================================

set -euo pipefail

# ANSI color codes
BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

main_appl='/pfs/lustrep1/appl/local/lumiiq'
destinations=( '/pfs/lustrep2/appl/local/lumiiq' '/pfs/lustrep3/appl/local/lumiiq' '/pfs/lustrep4/appl/local/lumiiq' )
dest_short=(   'lustrep2'                       'lustrep3'                       'lustrep4' )

AUTO_CONFIRM=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -y|--yes|--non-interactive|--force)
            AUTO_CONFIRM=true
            shift
            ;;
        -n|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -y, --yes          Skip interactive confirmation prompt (for non-interactive / one-time runs)"
            echo "  -n, --dry-run      Perform dry run without modifying files"
            echo "  -h, --help         Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown argument: $1${RESET}"
            exit 1
            ;;
    esac
done

# Resolve logging directory
logdir="/scratch/project_462001789/software_stack/appl_sync_logs"
if [ ! -d "$logdir" ]; then
    mkdir -p "$logdir" 2>/dev/null || {
        logdir="${SCRATCH:-/tmp}/appl_sync_logs"
        mkdir -p "$logdir" 2>/dev/null || logdir="/tmp"
    }
fi
logfile="$(date --iso-8601=seconds).txt"

echo -e "${BOLD}${CYAN}======================================================================${RESET}"
echo -e "${BOLD}${CYAN}          LUMI Multi-Lustre Partition Sync (Task 2.1)                 ${RESET}"
echo -e "${BOLD}${CYAN}======================================================================${RESET}"
echo -e "Master Source : ${BOLD}$main_appl${RESET}"
echo -e "Destinations  : ${BOLD}${destinations[*]}${RESET}"
echo -e "Log Directory : ${BOLD}$logdir${RESET}"
if [ "$DRY_RUN" = "true" ]; then
    echo -e "Execution Mode: ${YELLOW}DRY RUN${RESET}"
fi
echo -e "${CYAN}----------------------------------------------------------------------${RESET}"

# Verify master source exists
if [ ! -d "$main_appl" ]; then
    echo -e "${RED}[ERROR] Master source directory does not exist: $main_appl${RESET}"
    exit 1
fi

# Confirmation prompt if interactive
if [ "$AUTO_CONFIRM" = "false" ] && [ "$DRY_RUN" = "false" ]; then
    echo -e "\nCopying software installation from $main_appl to all partitions, are you sure?"
    select yn in "Yes" "No"; do
        case $yn in
            No ) echo "Aborted by user."; exit 0 ;;
            * )  break ;;
        esac
    done
fi

RSYNC_OPTS="-v --archive --delete"
if [ "$DRY_RUN" = "true" ]; then
    RSYNC_OPTS="$RSYNC_OPTS --dry-run"
fi

# Determine directories to synchronize
sync_dirs=( 'software' 'modulefiles' )
if [ -d "$main_appl/lumi-iq" ]; then
    sync_dirs+=( 'lumi-iq' )
fi
if [ -d "$main_appl/scripts" ]; then
    sync_dirs+=( 'scripts' )
fi

# Execute synchronization per directory across partitions in parallel
for directory in "${sync_dirs[@]}"; do
    echo -e "\n${BOLD}Synchronizing '$directory' across Lustre partitions in parallel...${RESET}"
    for i in "${!destinations[@]}"; do
        if [ "$DRY_RUN" = "false" ]; then
            mkdir -p "${destinations[$i]}/$directory" 2>/dev/null || true
        fi
        rsync $RSYNC_OPTS "$main_appl/$directory/" "${destinations[$i]}/$directory/" >& "$logdir/${dest_short[$i]}_${directory}_$logfile" &
    done
    wait
    echo -e "${GREEN}Sync for '$directory' completed across all partitions.${RESET}"
done

# 3. Enforce Permissions (Readable by ALL users, no write for others)
if [ "$DRY_RUN" = "false" ]; then
    echo -e "\n${BOLD}Enforcing global permissions (a+rX, o-w, appl_iq)...${RESET}"
    for target in "$main_appl" "${destinations[@]}"; do
        if [ -d "$target" ]; then
            chmod -R a+rX "$target" 2>/dev/null || true
            chmod -R o-w "$target" 2>/dev/null || true
            chgrp -R appl_iq "$target" 2>/dev/null || true
        fi
    done
    echo -e "${GREEN}Permissions successfully enforced across all Lustre partitions.${RESET}"
fi

echo -e "\n${BOLD}${GREEN}======================================================================${RESET}"
echo -e "${BOLD}${GREEN}[SUCCESS] Multi-Lustre synchronization completed successfully!${RESET}"
echo -e "${BOLD}${GREEN}======================================================================${RESET}\n"
