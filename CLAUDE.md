# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Recipe management system with:
- Recipe storage in markdown format (`data/recipes/*.md`)
- Structured extraction to JSON via OpenAI API
- Semantic search using sentence-transformers (jina-embeddings-v5)
- vLLM server for LLM processing

## Dependencies

Managed by `uv` and Python 3.13. Install: `uv sync`

## Running Servers

- vLLM: `./utils/launch_vllm_server.sh` (OpenAI-compatible API on :8000)
- Search: `./utils/launch_search_server.sh` (Gradio API with embeddings)

## Data Flow

1. Recipe MD files → `main.py` extracts structured info → JSON output
2. Recipe JSONs → `utils/search.py` loads and creates embeddings
3. Embeddings enable semantic search for recipes

## Key Files

- `main.py`: Extract recipes from MD using OpenAI's structured output (Pydantic)
- `utils/search.py`: Load JSON recipes, compute embeddings with SentenceTransformer, provide search API
- `utils/convert_to_markdown.py`: Recipe markdown conversion utilities
