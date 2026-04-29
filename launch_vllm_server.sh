#!/bin/bash

uv run vllm serve \
    --model google/gemma-4-E4B-it \
    --host 0.0.0.0 \
    --port 3960 \
    --quantization bitsandbytes \
    --max-model-len 131072 \
    --language-model-only