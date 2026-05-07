# connect-care

A recipe management system that transforms unstructured recipe sources ([PDFs](https://en.wikipedia.org/wiki/PDF), web pages) into structured, searchable recipe data. The system uses [LLM](https://en.wikipedia.org/wiki/Large_language_model)-based extraction to parse recipes into structured [JSON](https://en.wikipedia.org/wiki/JSON) format, translates them into multiple languages (English, Spanish, Catalan, Danish), and provides semantic search capabilities via vector embeddings. Built with [Gradio](https://gradio.app/) and exposed via [MCP](https://modelcontextprotocol.io/docs/getting-started/intro) for AI assistant integration.

## Prerequisites

- [transformer branch](https://github.com/aislab-hevs/tutorials/tree/transformer): a curated collection of learning resources on the [transformer](https://en.wikipedia.org/wiki/Transformer_(deep_learning)) architecture behind [LLMs](https://en.wikipedia.org/wiki/Large_language_model)
- [workstation branch](https://github.com/aislab-hevs/tutorials/tree/workstation): how to connect to a Z4 workstation via [SSH](https://en.wikipedia.org/wiki/Secure_Shell) and set up [VS Code:](https://code.visualstudio.com/) for remote development
- [uv branch](https://github.com/aislab-hevs/tutorials/tree/uv): how to use [uv](https://docs.astral.sh/uv/) for Python package management
- [gradio branch](https://github.com/aislab-hevs/tutorials/tree/gradio): how to build a simple greeting app using [Gradio](https://gradio.app/)
- [mcp branch](https://github.com/aislab-hevs/tutorials/tree/mcp): how to build a simple addition API using [Gradio](https://gradio.app/) and expose it via [MCP](https://modelcontextprotocol.io/docs/getting-started/intro) for an AI assistant
- [vllm branch](https://github.com/aislab-hevs/tutorials/tree/vllm): how to launch a [vLLM](https://docs.vllm.ai/en/latest/) server as an alternative to [llama.cpp](https://github.com/ggml-org/llama.cpp)
- [json branch](https://github.com/aislab-hevs/tutorials/tree/json): how to use [vLLM](https://docs.vllm.ai/en/latest/) with structured JSON outputs for recipe extraction
- [rag branch](https://github.com/aislab-hevs/tutorials/tree/rag): how to build a semantic search system using vector embeddings, built with [Gradio](https://gradio.app/) and exposed via [MCP](https://modelcontextprotocol.io/docs/getting-started/intro) for an AI assistant

To sync dependencies, run the following command:
```bash
uv sync
```

## Workflow

Contact Jean-Paul or Gaetano to obtain the recipe data folder. Place the received `recipes` folder inside the `data/` directory.

### Convert to Markdown

Convert PDF and TXT files (containing URLs to web recipes) to Markdown format:

```bash
bash launch_convert_to_markdown.sh
```

This processes all `*.pdf` and `*.txt` files in `data/recipes/` and creates corresponding `.md` files.

### Start vLLM Server

Ensure the [vLLM](https://vllm.ai) server is running in the background (e.g., separate terminal):

```bash
bash launch_vllm_server.sh
```

### Extract Recipes

Extract structured recipe information from the Markdown files:

```bash
bash launch_extract_recipes.sh
```

This processes all `*.md` files in `data/recipes/` and creates corresponding `.source.<language>.json` files with structured recipe data in the source language.

### Translate Recipes

Translate extracted recipes into multiple target languages:

```bash
bash launch_translate_recipes.sh
```

This reads all `.source.<language>.json` files and generates `.target.<language>.json` files for each target language (English, Spanish, Catalan, Danish by default).

### Merge Recipes by Language

Merge all recipe JSON files into per-language JSONL files:

```bash
bash launch_merge_recipes.sh
```

This combines `.source.*.json` and `.target.*.json` files into `data/recipes.<language>.jsonl` files (e.g., `data/recipes.en.jsonl`, `data/recipes.es.jsonl`, `data/recipes.ca.jsonl`, `data/recipes.da.jsonl`).

### Launch Search Server

Launch the semantic search server:

```bash
API_TOKEN="connect-care" bash launch_search_server.sh
```

To enable GPU acceleration, uncomment the `--cuda` flag in `launch_search_server.sh`.

Optionally set the `API_TOKEN` environment variable to enable authentication for the search API. This value must be provided as the token in requests to access the search endpoints.

This starts a [Gradio](https://gradio.app/)-based search server with [MCP](https://modelcontextprotocol.io/docs/getting-started/intro) support. The server loads recipes from language JSONL files, computes embeddings per language, and exposes both a web UI and API endpoints for searching recipes. Supported languages are English (`en`), Spanish (`es`), Catalan (`ca`), and Danish (`da`). Use the `language` parameter to filter results by language (defaults to `"en"`).

Two access options are available:
- Localhost: use `http://127.0.0.1:7860` for local access.
- Gradio live: the server prints a public URL. Replace `xxxxx` in `https://xxxxx.gradio.live` with the hash printed by the server to construct the API URL.

Example usage with `curl`:

```bash
QUERY="cheesecake"
TOP_K=1
API_TOKEN="connect-care"
ADDRESS="http://127.0.0.1:7860"
# ADDRESS="https://xxxxx.gradio.live"

EVENT_ID=$(
  curl -X POST $ADDRESS/gradio_api/call/v2/search \
    -s \
    -H "Content-Type: application/json" \
    -H "X-Api-Token: $API_TOKEN" \
    -d "{\"query\": \"$QUERY\", \"top_k\": $TOP_K, \"language\": \"en\"}" \
  | awk -F'"' '{print $4}'
)

curl -N $ADDRESS/gradio_api/call/v2/search/$EVENT_ID \
  | grep '^data:' \
  | sed 's/^data: //' \
  | jq -r '.[0]'
```
