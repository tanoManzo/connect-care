#!/bin/bash

uv run vllm serve \
    --model cyankiwi/gemma-4-26B-A4B-it-AWQ-4bit \
    --host 0.0.0.0 \
    --port 3960 \
    --max-model-len 32768 \
    --kv-cache-dtype fp8 \
    --language-model-only \
    --max-num-seqs 4 \
    --gpu-memory-utilization 0.95