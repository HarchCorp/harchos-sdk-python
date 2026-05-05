#!/usr/bin/env bash
# Example: HarchOS CLI usage
#
# Install: pip install harchos
# Set API key: export HARCHOS_API_KEY=hsk_your_api_key_here

set -e

echo "=== HarchOS CLI Demo ==="
echo ""

# Check API status
echo "1. Checking API status..."
harchos status

# Check carbon intensity
echo "2. Carbon intensity for Morocco..."
harchos carbon MA

# List all carbon zones
echo "3. All carbon zones..."
harchos carbon

# List hubs
echo "4. Sovereign compute hubs..."
harchos hubs

# List models
echo "5. Available AI models..."
harchos models

# Run carbon optimizer
echo "6. Carbon-aware optimization..."
harchos optimize --name "my-training-job" --gpus 4 --gpu-type A100 --region morocco

# Green scheduling windows
echo "7. Green scheduling windows..."
harchos green-windows --region morocco

# Show configuration
echo "8. Current configuration..."
harchos config show

echo ""
echo "=== Demo complete! ==="
