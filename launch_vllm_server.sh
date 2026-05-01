#!/bin/bash

uv run vllm serve cyankiwi/Ministral-3-14B-Instruct-2512-AWQ-4bit \
  --tokenizer_mode mistral \
  --config_format mistral \
  --load_format mistral \
  --enable-auto-tool-choice \
  --tool-call-parser mistral \
  --port 3960 \
  --max-model-len 49152 \
  --gpu-memory-utilization 0.95 \
  --language-model-only