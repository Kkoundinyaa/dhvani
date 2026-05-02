#!/bin/bash
#SBATCH --job-name=dhwani-large
#SBATCH --account=PAS2836
#SBATCH --time=03:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --output=logs/expand-large-%j.out
#SBATCH --error=logs/expand-large-%j.err

# =============================================================
# dhwani LARGE lexicon expansion
# Step 1: Extract words from MASSIVE + XNLI (expected 50K-100K unique words)
# Step 2: Generate romanized variants for ALL of them
# Estimated: ~30-60 minutes total
# =============================================================

echo "=========================================="
echo "dhwani LARGE lexicon expansion"
echo "Started: $(date)"
echo "Node: $(hostname)"
echo "=========================================="

module load miniconda3
source activate base

cd /users/PAS2836/krishnakb/ondemand/krishna_proj/dhwani
mkdir -p logs

# Step 1: Extract words from all Hindi datasets
echo ""
echo "[Step 1/2] Extracting Devanagari words from MASSIVE + XNLI..."
python scripts/extract_from_datasets.py

# Step 2: Generate romanized variants
echo ""
echo "[Step 2/2] Generating romanized variants..."
python scripts/expand_lexicon.py \
    --devanagari data/devanagari_words_large.txt \
    --output dhwani/lexicon/ \
    --max-variants 6 \
    --merge

echo ""
echo "=========================================="
echo "Final lexicon size:"
python -c "
import json
with open('dhwani/lexicon/correction_map.json') as f:
    cm = json.load(f)
with open('dhwani/lexicon/ipa_map.json') as f:
    im = json.load(f)
print(f'  Correction map: {len(cm):,} entries')
print(f'  IPA map: {len(im):,} entries')
"
echo "Completed: $(date)"
echo "=========================================="
