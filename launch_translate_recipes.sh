#!/usr/bin/env bash

uv run utils/translate_recipes.py \
    --recipe-dir data/recipes \
    --max-workers 12 \
    --target-languages "en,es,ca,da" \