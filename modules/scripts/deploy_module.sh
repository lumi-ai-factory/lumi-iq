#!/bin/bash
# ==============================================================================
# LUMI-IQ Master Module Deployment Script
# Supports:
#   1. System-wide deployment to /appl/local/lumiiq (default)
#   2. Project-level shared deployment to /project/<project_id>
#   3. User-level sandbox deployment to $HOME/lumi-iq-env
#
# Usage:
#   bash deploy_module.sh [--appl | --project <PROJECT_ID> | --user] [--build]
# ==============================================================================

set -euo pipefail

BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULES_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DEPLOY_TARGET="appl"
PROJECT_ID="${LUMI_PROJECT:-}"
DO_BUILD=false
DRY_RUN=false
RECIPE_FILE="$MODULES_ROOT/recipes/env-initial.yml"

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --appl)
            DEPLOY_TARGET="appl"
            shift
            ;;
        --project)
            DEPLOY_TARGET="project"
            PROJECT_ID="$2"
            shift 2
            ;;
        --user)
            DEPLOY_TARGET="user"
            shift
            ;;
        --build)
            DO_BUILD=true
            shift
            ;;
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --recipe)
            RECIPE_FILE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --appl                 Deploy system-wide to /appl/local/lumiiq (default)"
            echo "  --project <ID>         Deploy to shared project storage (/project/<ID>)"
            echo "  --user                 Deploy to personal home directory ($HOME/lumi-iq-env)"
            echo "  --build                Force rebuild of Tykky container"
            echo "  --dry-run, -n          Simulate deployment steps and test permissions without writing changes"
            echo "  --recipe <FILE>        Specify custom environment recipe file"
            exit 0
            ;;
        *)
            if [ -z "$PROJECT_ID" ] && [[ "$1" != --* ]]; then
                DEPLOY_TARGET="project"
                PROJECT_ID="$1"
                shift
            else
                echo -e "${RED}Unknown argument: $1${RESET}"
                exit 1
            fi
            ;;
    esac
done

# Resolve paths based on deployment target
if [ "$DEPLOY_TARGET" = "appl" ]; then
    STAGING_ROOT="/pfs/lustrep1/appl/local/lumiiq"
    PRODUCTION_ROOT="/appl/local/lumiiq"
    SW_DIR="$STAGING_ROOT/software/lumi-iq-env"
    MODULE_DIR="$STAGING_ROOT/modulefiles"
    IS_SYSTEM=true
elif [ "$DEPLOY_TARGET" = "project" ]; then
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}[ERROR] Project ID not specified. Use: --project <PROJECT_ID>${RESET}"
        exit 1
    fi
    STAGING_ROOT="/project/${PROJECT_ID}"
    if [ ! -d "$STAGING_ROOT" ] && [ -d "/scratch/${PROJECT_ID}" ]; then
        STAGING_ROOT="/scratch/${PROJECT_ID}"
    fi
    PRODUCTION_ROOT="$STAGING_ROOT"
    SW_DIR="$STAGING_ROOT/software/lumi-iq-env"
    MODULE_DIR="$STAGING_ROOT/modulefiles"
    IS_SYSTEM=false
else # user
    STAGING_ROOT="$HOME"
    PRODUCTION_ROOT="$HOME"
    SW_DIR="$HOME/lumi-iq-env"
    MODULE_DIR="$HOME/modulefiles"
    IS_SYSTEM=false
fi

echo -e "${BOLD}${CYAN}======================================================================${RESET}"
echo -e "${BOLD}${CYAN}               LUMI-IQ Module Deployment Pipeline                     ${RESET}"
echo -e "${BOLD}${CYAN}======================================================================${RESET}"
echo -e "Target Scope     : ${BOLD}$DEPLOY_TARGET${RESET}"
echo -e "Software Target  : ${BOLD}$SW_DIR${RESET}"
echo -e "Modulefiles Root : ${BOLD}$MODULE_DIR${RESET}"
echo -e "Build Trigger    : ${BOLD}$DO_BUILD${RESET}"
echo -e "Recipe File      : ${BOLD}$RECIPE_FILE${RESET}"
echo -e "${CYAN}----------------------------------------------------------------------${RESET}"

# Dry Run Simulation
if [ "$DRY_RUN" = "true" ]; then
    echo -e "${BOLD}${YELLOW}=== DRY RUN SIMULATION (No files or containers will be written) ===${RESET}"
    echo ""
    echo "1. Checking recipe file:"
    if [ -f "$RECIPE_FILE" ]; then
        echo -e "   Recipe found: ${GREEN}$RECIPE_FILE${RESET}"
    else
        echo -e "   ${RED}[ERROR] Recipe file not found: $RECIPE_FILE${RESET}"
    fi

    echo "2. Checking Staging Directory write permissions ($STAGING_ROOT):"
    if [ -d "$STAGING_ROOT" ]; then
        if [ -w "$STAGING_ROOT" ]; then
            echo -e "   ${GREEN}[OK] Staging directory is writable.${RESET}"
        else
            echo -e "   ${RED}[WARNING] Staging directory $STAGING_ROOT is NOT writable by current user ($USER).${RESET}"
        fi
    else
        echo -e "   ${YELLOW}[NOTICE] Staging directory $STAGING_ROOT does not exist yet (will be created during build).${RESET}"
    fi

    if [ "$IS_SYSTEM" = "true" ]; then
        echo "3. Checking Production Directory write permissions ($PRODUCTION_ROOT):"
        if [ -d "$PRODUCTION_ROOT" ]; then
            if [ -w "$PRODUCTION_ROOT" ]; then
                echo -e "   ${GREEN}[OK] Production directory is writable.${RESET}"
            else
                echo -e "   ${RED}[WARNING] Production directory $PRODUCTION_ROOT is NOT writable by current user ($USER).${RESET}"
                echo -e "   ${YELLOW}Hint: If you lack permissions for /appl, use: bash modules/scripts/deploy_module.sh --project <PROJECT_ID> --build${RESET}"
            fi
        else
            echo -e "   ${YELLOW}[NOTICE] Production directory $PRODUCTION_ROOT does not exist yet.${RESET}"
        fi
        echo "4. Simulating synchronization preview:"
        if [ -d "$STAGING_ROOT" ]; then
            bash "$SCRIPT_DIR/sync_to_appl.sh" --source "$STAGING_ROOT" --target "$PRODUCTION_ROOT" --dry-run 2>&1 || true
        else
            echo -e "   ${YELLOW}[INFO] Staging directory will be populated during actual build before sync.${RESET}"
        fi
    fi

    echo ""
    echo -e "${BOLD}${GREEN}[DRY RUN COMPLETE] Deployment parameters validated successfully.${RESET}"
    exit 0
fi

# Step 1: Build Tykky container if requested or missing
if [ "$DO_BUILD" = "true" ] || [ ! -d "$SW_DIR" ]; then
    echo -e "${BOLD}[Step 1/3] Building Tykky container in staging directory...${RESET}"
    bash "$SCRIPT_DIR/build_module.sh" "$SW_DIR" "$RECIPE_FILE"
else
    echo -e "${GREEN}[Step 1/3] Existing software container detected in $SW_DIR.${RESET}"
fi

# Step 2: Copy modulefiles
echo -e "${BOLD}[Step 2/3] Installing modulefiles to $MODULE_DIR ...${RESET}"
mkdir -p "$MODULE_DIR"
cp -r "$MODULES_ROOT/modulefiles/"* "$MODULE_DIR/" 2>/dev/null || rsync -rlptDvh --omit-dir-times "$MODULES_ROOT/modulefiles/" "$MODULE_DIR/" || true

# If project/user scope, adapt env path in modulefiles
if [ "$IS_SYSTEM" = "false" ]; then
    sed -i "s|local base_root = \".*\"|local base_root = \"$PRODUCTION_ROOT\"|g" "$MODULE_DIR"/*/*.lua 2>/dev/null || true
    sed -i "s|local env_root  = .*|local env_root  = \"$SW_DIR\"|g" "$MODULE_DIR"/*/*.lua 2>/dev/null || true
    sed -i "s|Software Root: .*|Software Root: $SW_DIR|g" "$MODULE_DIR"/*/*.lua 2>/dev/null || true
fi

# Step 3: Synchronization (for system-wide deployment)
if [ "$IS_SYSTEM" = "true" ]; then
    echo -e "${BOLD}[Step 3/3] Synchronizing to production hierarchy /appl/local/lumiiq ...${RESET}"
    bash "$SCRIPT_DIR/sync_to_appl.sh" --source "$STAGING_ROOT" --target "$PRODUCTION_ROOT"
    bash "$SCRIPT_DIR/verify_module.sh" "$PRODUCTION_ROOT"
else
    echo -e "${BOLD}[Step 3/3] Setting permissions...${RESET}"
    chmod -R g+rX,o+rX "$SW_DIR" "$MODULE_DIR" 2>/dev/null || true
    bash "$SCRIPT_DIR/verify_module.sh" "$PRODUCTION_ROOT"
fi

echo -e "${BOLD}${GREEN}======================================================================${RESET}"
echo -e "${BOLD}${GREEN}[SUCCESS] Module deployment complete!${RESET}"
echo -e "${BOLD}${GREEN}======================================================================${RESET}"
echo -e "To load this module:"
echo -e "  ${CYAN}module use $MODULE_DIR${RESET}"
echo -e "  ${CYAN}module load Lumi-IQ-qaas/VLQ${RESET}"
