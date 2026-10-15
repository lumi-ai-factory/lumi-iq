#!/bin/bash
# ==============================================================================
# Register LUMI-IQ Tykky Environment as Jupyter Kernel on LUMI Open OnDemand
# URL: https://www.lumi.csc.fi
# ==============================================================================

set -euo pipefail

ENV_DIR="${1:-$HOME/lumi-iq-env}"
KERNEL_NAME="lumi-iq-vlq"
KERNEL_DISPLAY="LUMI-IQ (Python 3.12 - VLQ Quantum)"

echo "Registering Jupyter kernel for LUMI Open OnDemand..."

# Target kernel directory in user's home
KERNEL_DIR="$HOME/.local/share/jupyter/kernels/$KERNEL_NAME"
mkdir -p "$KERNEL_DIR"

cat <<EOF > "$KERNEL_DIR/kernel.json"
{
  "argv": [
    "$ENV_DIR/bin/python",
    "-m",
    "ipykernel_launcher",
    "-f",
    "{connection_file}"
  ],
  "display_name": "$KERNEL_DISPLAY",
  "language": "python"
}
EOF

echo "Kernel registered successfully at: $KERNEL_DIR"
echo "You can now select '$KERNEL_DISPLAY' in JupyterLab on www.lumi.csc.fi"
