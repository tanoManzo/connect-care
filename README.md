# connect-care

Recipe management system with:
- Recipe storage in markdown format (`data/recipes/*.md`)
- Structured extraction to JSON via OpenAI API
- Semantic search using sentence-transformers
- vLLM server for LLM processing

## Getting Started

### 1. Convert Recipe Files to Markdown

If you have recipe files in PDF or TXT format (containing URLs), convert them to markdown first:

```bash
uv run utils/convert_to_markdown.py
```

### 2. Extract Recipe Information

First, start the vLLM server:

```bash
./utils/launch_vllm_server.sh
```

Then extract structured recipe information from the markdown files:

```bash
uv run utils/extract_recipes.py
```

This processes all `*.md` files in `data/recipes/` and creates corresponding JSON files with structured recipe data.

### 3. Launch Search Server

For semantic search functionality:

```bash
./utils/launch_search_server.sh
```

This starts a Gradio API server with embeddings for searching recipes and includes MCP server support.

## Data Flow

1. Recipe files (PDF/TXT) → `convert_to_markdown.py` → Markdown files
2. Recipe MD files → `extract_recipes.py` → JSON output (using vLLM)
3. Recipe JSONs → `search.py` → Embeddings → Search API

## Key Files

- `utils/convert_to_markdown.py`: Recipe file format conversion utilities
- `utils/extract_recipes.py`: Structured recipe extraction using Pydantic models and OpenAI API
- `utils/search.py`: Load JSON recipes, compute embeddings with sentence-transformer
- `utils/launch_vllm_server.sh`: Launch script for vLLM server
- `utils/launch_search_server.sh`: Launch script for search server