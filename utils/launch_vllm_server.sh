#!/usr/bin/env bash

# Launch script for vLLM server
echo "Launching vLLM server..."

# Start the vLLM server
uv run vllm serve cyankiwi/Ministral-3-14B-Instruct-2512-AWQ-4bit \
  --tokenizer_mode mistral \
  --config_format mistral \
  --load_format mistral \
  --enable-auto-tool-choice \
  --tool-call-parser mistral \
  --port 8000 \
  --max-model-len 40960
