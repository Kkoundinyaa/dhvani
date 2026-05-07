#!/bin/bash
# Deploy dhvani demo to HuggingFace Spaces
# Usage: bash demo/deploy_to_hf.sh
#
# Prerequisites:
#   1. pip install huggingface_hub
#   2. huggingface-cli login (get token from https://huggingface.co/settings/tokens)
#   3. Create a Space at https://huggingface.co/new-space
#      - Choose "Docker" as SDK
#      - Name it "dhvani"
#
# Then run this script to push everything.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
DEPLOY_DIR="$SCRIPT_DIR/deploy"

echo "=== Assembling deploy folder ==="

# Copy static files
rm -rf "$DEPLOY_DIR/static" "$DEPLOY_DIR/data"
cp -r "$SCRIPT_DIR/static" "$DEPLOY_DIR/static"

# Copy search index
mkdir -p "$DEPLOY_DIR/data"
cp "$REPO_DIR/data/search_index.json" "$DEPLOY_DIR/data/"

echo "Deploy folder ready at: $DEPLOY_DIR"
echo ""
echo "Files:"
find "$DEPLOY_DIR" -type f | sort
echo ""
echo "=== Next steps ==="
echo "1. Create a HuggingFace Space (Docker SDK) at https://huggingface.co/new-space"
echo "2. Clone it:  git clone https://huggingface.co/spaces/YOUR_USERNAME/dhvani"
echo "3. Copy files: cp -r $DEPLOY_DIR/* ./dhvani/"
echo "4. Push:      cd dhvani && git add . && git commit -m 'deploy' && git push"
echo ""
echo "Or use the HF CLI:"
echo "  huggingface-cli upload YOUR_USERNAME/dhvani $DEPLOY_DIR . --repo-type space"
