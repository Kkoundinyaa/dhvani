#!/bin/bash
#SBATCH --job-name=dhwani-expand
#SBATCH --account=PAS2836
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=logs/expand-lexicon-%j.out
#SBATCH --error=logs/expand-lexicon-%j.err

# =============================================================
# dhwani lexicon EXPANSION
# Takes 10K Devanagari words -> generates romanized variants
# Only needs epitran (no IndicXlit model), very fast
# Estimated: ~10-15 minutes for 10K words
# =============================================================

echo "=========================================="
echo "dhwani lexicon expansion"
echo "Started: $(date)"
echo "Node: $(hostname)"
echo "=========================================="

module load miniconda3
source activate base

cd /users/PAS2836/krishnakb/ondemand/krishna_proj/dhwani
mkdir -p logs

echo ""
echo "Generating romanized variants for 10K Devanagari words..."
echo "Max 6 variants per word -> up to 60K new entries"
echo ""

python scripts/expand_lexicon.py \
    --devanagari data/devanagari_words.txt \
    --output dhwani/lexicon/ \
    --max-variants 6 \
    --merge

echo ""
echo "=========================================="
echo "Completed: $(date)"
echo "=========================================="
