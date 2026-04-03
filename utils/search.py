# ----------------------------------------------------------------------------------------------------
import os
import json
import torch
import gradio as gr
# ----------------------------------------------------------------------------------------------------
from pathlib import Path
from sentence_transformers import SentenceTransformer
# ----------------------------------------------------------------------------------------------------
MODEL_NAME="jinaai/jina-embeddings-v5-text-nano-retrieval"
# MODEL_NAME="jinaai/jina-embeddings-v5-text-small-retrieval"
BATCH_SIZE=2
TRUNCATE_DIM=None
API_TOKEN = os.environ.get("API_TOKEN", None)
# ----------------------------------------------------------------------------------------------------
RECIPES = []
RECIPES_TO_TEXT = []
recipes_directory = Path("data/recipes")
for json_file in recipes_directory.rglob("*.json"):                                         
    with open(json_file, "r", encoding="utf-8") as input_file:
        recipe = json.load(input_file)
        RECIPES.append(recipe)                              
        RECIPES_TO_TEXT.append(f"```json\n{recipe}\n```")
MODEL = SentenceTransformer(
    MODEL_NAME,
    model_kwargs={"dtype": torch.bfloat16},
    truncate_dim=TRUNCATE_DIM,
    trust_remote_code=True
).to("cuda")
DOCUMENTS_EMBEDDING = torch.vstack(
    MODEL.encode(
        RECIPES_TO_TEXT,
        batch_size=BATCH_SIZE,
        prompt_name="document",
        convert_to_numpy=False,
        show_progress_bar=True
    )
)
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

    if (
        x_api_token != API_TOKEN or
        query is None or
        query == "" or
        top_k is None or
        top_k <= 0
    ):
        return

    query_embedding = MODEL.encode(
        query,
        prompt_name="query",
        convert_to_numpy=False
    )

    similarities = MODEL.similarity(
        query_embedding,
        DOCUMENTS_EMBEDDING
    ).squeeze()

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
    return search(query, top_k, x_api_token=token)
# ----------------------------------------------------------------------------------------------------
with gr.Blocks() as demo:
    gr.api(search, api_name="search")
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