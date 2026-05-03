#!/bin/bash
#SBATCH --job-name=dhwani-expand-v2
#SBATCH --account=PAS2836
#SBATCH --time=06:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --output=logs/expand-v2-%j.out
#SBATCH --error=logs/expand-v2-%j.err

# =============================================================
# dhwani MASSIVE lexicon expansion v2
# Sources: Hindi Wikipedia (50K articles) + IITB (500K sentences)
#        + existing words + social media slang
# Target: 500K-1M lexicon entries
# Estimated: 2-4 hours
# =============================================================

echo "=========================================="
echo "dhwani lexicon expansion v2"
echo "Started: $(date)"
echo "Node: $(hostname)"
echo "=========================================="

source /users/PAS2836/krishnakb/ondemand/krishna_proj/cleanenv/bin/activate

cd /users/PAS2836/krishnakb/ondemand/krishna_proj/dhwani
mkdir -p logs

echo ""
echo "Current lexicon size:"
python -c "
import json
with open('dhwani/lexicon/correction_map.json') as f:
    cm = json.load(f)
print(f'  Before: {len(cm):,} entries')
"

echo ""
echo "Running expand_lexicon_v2.py..."
python scripts/expand_lexicon_v2.py \
    --max-wiki-articles 50000 \
    --max-iitb-sentences 500000 \
    --max-variants 10 \
    --min-freq 2

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
