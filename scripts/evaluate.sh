#!/bin/bash
# HRPO-X Evaluation Script

set -e

CHECKPOINT=${1:-outputs/hrpo-x-v2.2f/checkpoints/best}
TEST_DATA=${2:-data/test.jsonl}
OUTPUT=${3:-outputs/eval_results.json}

echo "[>] Starting HRPO-X Evaluation"
echo "[=] Checkpoint: $CHECKPOINT"
echo "[=] Test Data: $TEST_DATA"
echo "[=] Output: $OUTPUT"

python -m training.evaluate \
    --checkpoint $CHECKPOINT \
    --test_data $TEST_DATA \
    --output $OUTPUT \
    --batch_size 16

echo "[+] Evaluation complete!"
echo "[L] Results saved to: $OUTPUT"
