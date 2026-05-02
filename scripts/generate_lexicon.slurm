#!/bin/bash
#SBATCH --job-name=dhwani-lexicon
#SBATCH --account=PAS2836
#SBATCH --time=04:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --output=logs/lexicon-gen-%j.out
#SBATCH --error=logs/lexicon-gen-%j.err

# =============================================================
# dhwani lexicon generation
# NO GPU needed - IndicXlit (11M params) runs fine on CPU
# Estimated time: ~2-3 hours for 10K+ words
# =============================================================

echo "=========================================="
echo "dhwani lexicon generation"
echo "Started: $(date)"
echo "Node: $(hostname)"
echo "=========================================="

# Setup
module load miniconda3
source activate base

cd /users/PAS2836/krishnakb/ondemand/krishna_proj/dhwani
mkdir -p logs

# Step 1: Extract words from datasets
echo ""
echo "[Step 1/3] Extracting words from datasets..."
python scripts/extract_hindi_words.py

# Step 2: Generate lexicon from romanized words
echo ""
echo "[Step 2/3] Generating lexicon (romanized -> devanagari -> IPA)..."
python scripts/generate_lexicon.py \
    --romanized data/romanized_words.txt \
    --devanagari data/devanagari_words.txt \
    --output dhwani/lexicon/hinglish_lexicon.json

# Step 3: Report
echo ""
echo "[Step 3/3] Results:"
echo "  Lexicon: $(wc -l < dhwani/lexicon/hinglish_lexicon.json) lines"
echo "  Correction map: $(wc -l < dhwani/lexicon/correction_map.json) lines"
echo "  IPA map: $(wc -l < dhwani/lexicon/ipa_map.json) lines"

echo ""
echo "=========================================="
echo "Completed: $(date)"
echo "=========================================="
