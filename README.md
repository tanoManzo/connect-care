# connect-care

A recipe management system that transforms unstructured recipe sources ([PDFs](https://en.wikipedia.org/wiki/PDF), web pages) into structured, searchable recipe data. The system uses [LLM](https://en.wikipedia.org/wiki/Large_language_model)-based extraction to parse recipes into multilingual [JSON](https://en.wikipedia.org/wiki/JSON) format (English, Spanish, Catalan, Danish) and provides semantic search capabilities via vector embeddings. Built with [Gradio](https://gradio.app/) and exposed via [MCP](https://modelcontextprotocol.io/docs/getting-started/intro) for AI assistant integration.

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

Contact **Jean-Paul** or **Gaetano** to obtain the recipe data folder. Place the received `recipes` folder inside the `data/` directory.

Convert PDF and TXT files (containing URLs to web recipes) to Markdown format:

```bash
bash launch_convert_to_markdown.sh
```

This processes all `*.pdf` and `*.txt` files in `data/recipes/` and creates corresponding `.md` files.

Next, ensure the vLLM server is running in the background (e.g., separate terminal):

```bash
bash launch_vllm_server.sh
```

Then extract structured recipe information from the Markdown files:

```bash
bash launch_extract_recipes.sh
```

This processes all `*.md` files in `data/recipes/` and creates corresponding `.json` files with structured, multilingual recipe data.

Merge all recipe JSON files into a single JSONL file:

```bash
bash launch_merge_recipes.sh
```

This combines all `.json` files into `data/recipes.jsonl` for efficient loading by the search server.

Finally, for semantic search functionality, launch the search server:

```bash
bash launch_search_server.sh
```

This starts a [Gradio](https://gradio.app/)-based search server with [MCP](https://modelcontextprotocol.io/docs/getting-started/intro) support. The server loads recipes from the JSONL file, computes embeddings, and exposes both a web UI and API endpoints for searching recipes.
