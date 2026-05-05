# ----------------------------------------------------------------------------------------------------
# Semantic search server for recipe data using sentence transformers
# Provides both API and UI endpoints via Gradio for searching recipes
# ----------------------------------------------------------------------------------------------------
import os
import json
import torch
import argparse
import gradio as gr
# ----------------------------------------------------------------------------------------------------
from pathlib import Path
from sentence_transformers import SentenceTransformer
# ----------------------------------------------------------------------------------------------------
# API token for authentication (set via environment variable)
API_TOKEN = os.environ.get("API_TOKEN", None)
# ----------------------------------------------------------------------------------------------------
# Global state variables (initialized in load_model_and_data)
MODEL = None  # Sentence transformer model
RECIPES = []  # List of recipe dictionaries
RECIPES_TO_TEXT = []  # String representations of recipes for embedding
DOCUMENTS_EMBEDDING = None  # Pre-computed embeddings of all recipes
# ----------------------------------------------------------------------------------------------------
def load_model_and_data(
    use_cuda: bool,
    batch_size: int,
    model_name: str,
    recipes_jsonl: str,
    truncate_dim,
):
    """Load the model and recipe data.

    Loads all recipes from one or more JSONL files,
    initializes the sentence transformer model, and pre-computes
    embeddings for all recipes.
    """
    global MODEL, DOCUMENTS_EMBEDDING, RECIPES, RECIPES_TO_TEXT

    # Resolve file paths (comma-separated string or single path)
    jsonl_paths = [
        p.strip() for p in recipes_jsonl.split(",")
    ]

    # Load recipes from all JSONL files
    for jsonl_path in jsonl_paths:
        with open(jsonl_path, "r", encoding="utf-8") as jsonl_file:
            for line in jsonl_file:
                recipe = json.loads(line.strip())
                RECIPES.append(recipe)
                RECIPES_TO_TEXT.append(f"```json\n{recipe}\n```")

    # Initialize sentence transformer model
    device = "cuda" if use_cuda else "cpu"
    MODEL = SentenceTransformer(
        model_name,
        device=device,
        truncate_dim=truncate_dim,
        trust_remote_code=True
    )

    # Encode all recipe documents into embeddings
    DOCUMENTS_EMBEDDING = torch.vstack(
        MODEL.encode(
            RECIPES_TO_TEXT,
            batch_size=batch_size,
            prompt_name="document",
            convert_to_numpy=False,
            show_progress_bar=True
        )
    )

    # Free CUDA memory after encoding if using GPU
    if use_cuda:
        torch.cuda.empty_cache()
# ----------------------------------------------------------------------------------------------------
def search(
    query: str,
    top_k: int = 5,
    x_api_token: gr.Header = None,
) -> list:
    """
    Search for recipes similar to the query.

    Args:
        query (str): Search query
        top_k (int): Number of top results to return

    Returns:
        list: Top k recipe objects as dictionaries
    """

    # Validate API token and parameters
    if (
        (API_TOKEN is not None and x_api_token != API_TOKEN)
        or query is None
        or query == ""
        or top_k is None
        or top_k <= 0
    ):
        return

    # Encode the search query
    query_embedding = MODEL.encode(
        query,
        prompt_name="query",
        convert_to_numpy=False
    )

    # Calculate similarity scores between query and all documents
    similarities = MODEL.similarity(
        query_embedding,
        DOCUMENTS_EMBEDDING
    ).squeeze()

    # Get indices of top-k most similar documents
    top_indices = torch.topk(
        similarities,
        k=top_k
    ).indices.tolist()

    return [RECIPES[index] for index in top_indices]


def _search_ui(
    query: str,
    top_k: int = 5,
    token: str = None,
) -> list:
    """Wrapper function for UI search that converts token to header format."""
    return search(
        query=query,
        top_k=top_k,
        x_api_token=token,
    )
# ----------------------------------------------------------------------------------------------------
def main():
    """Main entry point for the search server."""
    # Setup command line argument parser
    parser = argparse.ArgumentParser(
        description="Recipe search with semantic embeddings"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="jinaai/jina-embeddings-v5-text-nano-retrieval",
        help="Model name to use (default: jinaai/jina-embeddings-v5-text-nano-retrieval)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=8,
        help="Batch size for encoding (default: 8)"
    )
    parser.add_argument(
        "--truncate-dim",
        type=lambda x: None if x.lower() == "none" else int(x),
        default=None,
        help="Dimension to truncate embeddings to (default: None for no truncation)"
    )
    parser.add_argument(
        "--cuda",
        dest="use_cuda",
        action="store_true",
        default=False,
        help="Enable CUDA for encoding (default: False)"
    )
    parser.add_argument(
        "--languages",
        type=str,
        default="en,es,ca,da",
        help="Comma-separated list of language codes for recipes (default: en,es,ca,da)"
    )
    parser.add_argument(
        "--recipes-dir",
        type=str,
        default="data",
        help="Directory containing recipes.<lang>.jsonl files (default: data)"
    )

    args = parser.parse_args()

    # Discover recipes.<lang>.jsonl files in the data directory
    languages = {language.strip() for language in args.languages.split(",")}
    data_dir = Path(args.recipes_dir)
    found = sorted(
        str(jsonl_path) for jsonl_path in data_dir.glob("recipes.*.jsonl")
        if jsonl_path.stem.startswith("recipes.")
        and jsonl_path.stem[len("recipes."):] in languages
    )
    recipes_jsonl = ",".join(found)

    # Load model and data
    load_model_and_data(
        use_cuda=args.use_cuda,
        batch_size=args.batch_size,
        model_name=args.model,
        recipes_jsonl=recipes_jsonl,
        truncate_dim=args.truncate_dim,
    )

    # Launch Gradio interface with API and UI
    with gr.Blocks() as demo:
        # Register search function as API endpoint
        gr.api(
            search,
            api_name="search",
        )

        # Build UI layout
        with gr.Row():
            token = gr.Textbox(
                label="Token",
                type="password",
                scale=1
            )
            input_textbox = gr.Textbox(
                label="Query",
                scale=8
            )
            topk_number = gr.Number(
                label="Top K",
                value=5,
                precision=0,
                scale=1
            )
        output_json = gr.JSON(label="Results")

        # Wire up event handlers
        input_textbox.change(
            _search_ui,
            inputs=[input_textbox, topk_number, token],
            outputs=output_json,
            api_name=False,
            show_progress=False
        )
        input_textbox.submit(
            _search_ui,
            inputs=[input_textbox, topk_number, token],
            outputs=output_json,
            api_name=False,
            show_progress=False
        )
        token.change(
            _search_ui,
            inputs=[input_textbox, topk_number, token],
            outputs=output_json,
            api_name=False,
            show_progress=False
        )
        topk_number.change(
            _search_ui,
            inputs=[input_textbox, topk_number, token],
            outputs=output_json,
            api_name=False,
            show_progress=False
        )
        demo.launch(
            share=True,
            mcp_server=True
        )
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------------------------------
