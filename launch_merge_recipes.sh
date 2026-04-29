#!/usr/bin/env bash

uv run utils/merge_recipes.py \
    --recipe-dir data/recipes \
    --output data/recipes.jsonl
