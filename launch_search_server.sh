#!/usr/bin/env bash

uv run utils/search_server.py \
    --model jinaai/jina-embeddings-v5-text-nano-retrieval \
    --batch-size 8 \
    --truncate-dim None \
    --cuda \
    --language en,es,ca,da
