#!/bin/bash

THREADS=$(nproc)

cd ~/llama.cpp/build/bin
./llama-server \
    -hf unsloth/Qwen3.6-35B-A3B-GGUF:UD-IQ4_NL \
    --alias "Qwen3.6-35B-A3B" \
    --port 3960 \
    --host 0.0.0.0 \
    --temp 0.6 \
    --top-p 0.95 \
    --top-k 20 \
    --min-p 0.0 \
    --threads $THREADS \
    --ctx-size 65536 \
    --reasoning false \
    --flash-attn on \
    --n-gpu-layers 99 \
    --cache-type-k q4_0 \
    --cache-type-v q4_0 \
    --no-cont-batching \
    --no-cache-prompt