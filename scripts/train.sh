#!/bin/bash
# HRPO-X Training Script

set -e

# Parse arguments
CONFIG=${1:-config/base_config.yaml}
OUTPUT_DIR=${2:-outputs/hrpo-x-v2.2f}
NUM_GPUS=${3:-1}

echo "[>] Starting HRPO-X v2.2f Training"
echo "[=] Config: $CONFIG"
echo "[=] Output: $OUTPUT_DIR"
echo "[=] GPUs: $NUM_GPUS"

# Create output directory
mkdir -p $OUTPUT_DIR

# Run training
if [ "$NUM_GPUS" -eq 1 ]; then
    python -m training.trainer \
        --config $CONFIG \
        --output_dir $OUTPUT_DIR \
        --logging_dir $OUTPUT_DIR/logs
else
    torchrun --nproc_per_node=$NUM_GPUS \
        -m training.trainer \
        --config $CONFIG \
        --output_dir $OUTPUT_DIR \
        --logging_dir $OUTPUT_DIR/logs
fi

echo "[+] Training complete!"
echo "[L] Logs saved to: $OUTPUT_DIR/logs"
echo "[L] Checkpoints saved to: $OUTPUT_DIR/checkpoints"
