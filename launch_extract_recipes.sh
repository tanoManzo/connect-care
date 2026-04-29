#!/usr/bin/env bash

uv run utils/extract_recipes.py \
    --recipe-dir data/recipes \
    --max-workers 8