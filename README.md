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

This starts a [Gradio](https://gradio.app/)-based search server with [MCP](https://modelcontextprotocol.io/docs/getting-started/intro) support. The server loads recipes from language JSONL files, computes embeddings per language, and exposes both a web UI and API endpoints for searching recipes. Supported languages are English (en), Spanish (es), Catalan (ca), and Danish (da). Use the `language` parameter to filter results by language (defaults to `"en"`).

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

### Personalized Recommendation Example

The recommendation server runs `AI_search.sh` internally. Colleagues only need its public URL, `curl`, and `jq`, not access to the backend services.

```bash
ADDRESS="https://tangy-pots-relax.loca.lt" \
USER_ID="user_001" \
QUERY="apple dessert for 2 people, no honey" \
sh connect_care_recommendation_example.sh
```

The JSON contains `recipe`, `updated_recipe`, `latest_calories_in`, and the full `recipes` and `updated_recipes` lists. Calories are fetched from the trajectory API for `USER_ID`; if unavailable, invalid, or timed out, calories default to `0`.

Alternatively, query the Gradio API directly:

```bash
ADDRESS="https://tangy-pots-relax.loca.lt"
EVENT_ID=$(curl -fsS "$ADDRESS/gradio_api/call/run_recipe_search" \
  -H "Content-Type: application/json" \
  -H "bypass-tunnel-reminder: true" \
  -d '{"data": ["user_001", "apple dessert for 2 people, no honey", "en", 3]}' \
  | jq -er '.event_id')
curl -fsSN "$ADDRESS/gradio_api/call/run_recipe_search/$EVENT_ID" \
  -H "bypass-tunnel-reminder: true" \
  | sed -n 's/^data: //p' | jq '.[0]'
```

The argument order is user ID, recipe query, output language (`en`, `es`, `ca`, or `da`), and `top_k` (positive integer; defaults to 3 in the shell example). The LocalTunnel URL above was started on 2026-10-23 and only works while the tunnel and backend services are running. It can change when the tunnel restarts; update the example's `ADDRESS` accordingly. This is a public, unauthenticated demo endpoint; do not send sensitive user information.

#### Running in tmux

From the project directory:

```bash
tmux new-session -d -s connect-care -n model 'bash launch_vllm_server.sh; exec bash'
tmux new-window -t connect-care -n search 'API_TOKEN=connect-care bash launch_search_server.sh; exec bash'
tmux new-window -t connect-care -n recommendations 'bash launch_ai_search_app.sh; exec bash'
tmux new-session -d -s connect-care-tunnel -n tunnel 'npx --yes localtunnel --port 7862 --local-host 127.0.0.1; exec bash'
tmux attach -t connect-care
```

Use `tmux attach -t connect-care-tunnel` to see the LocalTunnel URL to share. tmux survives SSH disconnects, not power outages; rerun the commands after a reboot. On the recommendation server, configure `USER_API_ADDRESS`, `SEARCH_API_ADDRESS`, and `LLM_API_ADDRESS` if needed (defaults: localhost ports 8000, 7860, and 3960). Wait for the model and search server to finish loading before querying recommendations.

### Move the Recommendation Service to a New Server

These steps move the current working tree and the existing recipe indexes to a Linux server with an NVIDIA GPU. Run the copy command on the current machine from the repository root. It includes modified and untracked project files, but skips rebuildable environments and caches:

```bash
rsync -av --info=progress2 \
  --exclude='.venv/' \
  --exclude='node_modules/' \
  --exclude='.gradio/' \
  --exclude='__pycache__/' \
  ./ USER@SERVER:/srv/connect-care/
```

Replace `USER` and `SERVER` with the SSH account and hostname. The four `data/recipes.*.jsonl` files are included. The raw source files under `data/recipes/` are not needed to serve the existing indexes; copy them separately if you also need to rerun extraction or translation.

On the new server, install a compatible NVIDIA driver, `uv`, `tmux`, `curl`, and `jq`. Confirm the GPU is visible with `nvidia-smi`, then install the locked Python dependencies:

```bash
cd /srv/connect-care
uv sync --frozen
```

Start the services in this order, each in its own terminal or tmux window:

```bash
# Model API on port 3960; first launch downloads the model from Hugging Face.
bash launch_vllm_server.sh

# Recipe search on port 7860. Set a private token rather than using the default.
API_TOKEN='REPLACE_WITH_A_PRIVATE_TOKEN' bash launch_search_server.sh

# Recommendation UI on port 7862.
API_TOKEN='REPLACE_WITH_A_PRIVATE_TOKEN' \
USER_API_ADDRESS='http://USER_API_HOST:8000' \
bash launch_ai_search_app.sh
```

Use the same `API_TOKEN` for the search and recommendation services. Replace `USER_API_HOST` with the host running the trajectory API; if it is unavailable, calorie lookup falls back to `0` and the user list falls back to `user_001`. The model and embedding models are downloaded on first use, so allow outbound access to Hugging Face and enough disk space for model weights. vLLM requires a GPU and driver combination supported by the installed vLLM release; verify compatibility for the destination GPU before relying on the default model.

Keep ports 3960, 7860, and 8000 restricted to localhost or the private network. The current Gradio launchers use `share=True`, which creates public, unauthenticated share URLs; do not use those URLs for sensitive data. Disable public sharing or put the UI behind an authenticated access layer before production use. The LocalTunnel URL from the old server will not transfer; create a new tunnel or configure a stable authenticated public endpoint for port 7862.
