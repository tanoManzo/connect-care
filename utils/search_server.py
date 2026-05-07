# ----------------------------------------------------------------------------------------------------
# Semantic search server for recipe data using sentence transformers
# Provides both API and UI endpoints via Gradio for searching recipes
# Supports per-language search with a 'language' parameter
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
RECIPES_BY_LANGUAGE = {}  # language -> list of recipe dicts
RECIPES_TO_TEXT_BY_LANGUAGE = {}  # language -> list of text representations
DOCUMENTS_EMBEDDING_BY_LANGUAGE = {}  # language -> pre-computed embeddings tensor
LANGUAGES = []  # sorted list of loaded language codes
# ----------------------------------------------------------------------------------------------------
def load_model_and_data(
    use_cuda: bool,
    languages: list,
    batch_size: int,
    model_name: str,
    recipes_dir: str,
    truncate_dim,
):
    """Load the model and recipe data.

    Loads recipes from JSONL files matching the given languages,
    initializes the sentence transformer model, and pre-computes
    embeddings per language.
    """
    global MODEL, DOCUMENTS_EMBEDDING_BY_LANGUAGE, RECIPES_BY_LANGUAGE, RECIPES_TO_TEXT_BY_LANGUAGE, LANGUAGES

    # Resolve file paths (comma-separated string or single path)
    data_dir = Path(recipes_dir)
    languages_set = {language.strip() for language in languages}
    found = sorted(
        jsonl_path for jsonl_path in data_dir.glob("recipes.*.jsonl")
        if jsonl_path.stem.startswith("recipes.")
        and jsonl_path.stem[len("recipes."):] in languages_set
    )
    LANGUAGES = sorted(language.strip() for language in languages)

    # Load recipes per language
    RECIPES_BY_LANGUAGE = {}
    RECIPES_TO_TEXT_BY_LANGUAGE = {}
    for jsonl_path in found:
        language = jsonl_path.stem[len("recipes."):]
        RECIPES_BY_LANGUAGE[language] = []
        RECIPES_TO_TEXT_BY_LANGUAGE[language] = []
        with open(jsonl_path, "r", encoding="utf-8") as jsonl_file:
            for line in jsonl_file:
                recipe = json.loads(line.strip())
                recipe_copy = dict(recipe)
                recipe_copy["target_language"] = language
                RECIPES_BY_LANGUAGE[language].append(recipe_copy)
                RECIPES_TO_TEXT_BY_LANGUAGE[language].append(f"```json\n{recipe}\n```")

    # Initialize sentence transformer model
    device = "cuda" if use_cuda else "cpu"
    MODEL = SentenceTransformer(
        model_name,
        device=device,
        truncate_dim=truncate_dim,
        trust_remote_code=True
    )

    # Encode each language's recipes separately
    for language in LANGUAGES:
        texts = RECIPES_TO_TEXT_BY_LANGUAGE[language]
        print(f"Encoding {language}...")
        DOCUMENTS_EMBEDDING_BY_LANGUAGE[language] = torch.vstack(
            MODEL.encode(
                texts,
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
    language: str = "en",
    x_api_token: gr.Header = None,
) -> list:
    """
    Search for recipes similar to the query.

    Args:
        query (str): Search query
        top_k (int): Number of top results to return
        language (str): Language code to filter results. One of: en, es, ca, da (default: "en")

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

    # Check that the requested language is available
    if language not in DOCUMENTS_EMBEDDING_BY_LANGUAGE:
        return

    # Encode the search query
    query_embedding = MODEL.encode(
        query,
        prompt_name="query",
        convert_to_numpy=False
    )

    # Calculate similarity scores against that language's embeddings
    similarities = MODEL.similarity(
        query_embedding,
        DOCUMENTS_EMBEDDING_BY_LANGUAGE[language]
    ).squeeze()

    # Get indices of top-k most similar documents
    k = min(top_k, len(similarities))
    top_indices = torch.topk(similarities, k=k).indices.tolist()

    return [RECIPES_BY_LANGUAGE[language][index] for index in top_indices]


def _search_ui(
    query: str,
    top_k: int = 5,
    language: str = "en",
    token: str = None,
) -> list:
    """Wrapper function for UI search that converts token to header format."""
    return search(
        query=query,
        top_k=top_k,
        language=language,
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

    # Parse languages from comma-separated string
    LANGUAGES = [language.strip() for language in args.languages.split(",")]

    # Load model and data
    load_model_and_data(
        use_cuda=args.use_cuda,
        languages=LANGUAGES,
        batch_size=args.batch_size,
        model_name=args.model,
        recipes_dir=args.recipes_dir,
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
                scale=7
            )
            language_dropdown = gr.Dropdown(
                choices=LANGUAGES,
                value="en" if "en" in LANGUAGES else (LANGUAGES[0] if LANGUAGES else ""),
                label="Language",
                scale=1
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
            inputs=[input_textbox, topk_number, language_dropdown, token],
            outputs=output_json,
            api_name=False,
            show_progress=False
        )
        input_textbox.submit(
            _search_ui,
            inputs=[input_textbox, topk_number, language_dropdown, token],
            outputs=output_json,
            api_name=False,
            show_progress=False
        )
        token.change(
            _search_ui,
            inputs=[input_textbox, topk_number, language_dropdown, token],
            outputs=output_json,
            api_name=False,
            show_progress=False
        )
        topk_number.change(
            _search_ui,
            inputs=[input_textbox, topk_number, language_dropdown, token],
            outputs=output_json,
            api_name=False,
            show_progress=False
        )
        language_dropdown.change(
            _search_ui,
            inputs=[input_textbox, topk_number, language_dropdown, token],
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
