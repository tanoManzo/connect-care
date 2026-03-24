# ----------------------------------------------------------------------------------------------------
import json
import torch
import gradio as gr
# ----------------------------------------------------------------------------------------------------
from pathlib import Path
from sentence_transformers import SentenceTransformer
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
    "jinaai/jina-embeddings-v5-text-small-retrieval",
    model_kwargs={"dtype": torch.bfloat16}
).to("cuda")
DOCUMENTS_EMBEDDING = torch.vstack(
    MODEL.encode(
        RECIPES_TO_TEXT,
        batch_size=64,
        prompt_name="document",
        convert_to_numpy=False,
    )
)
def search(
    query: str,
    top_k: int = 5
) -> list:
    """
    Search for recipes similar to the query.

    Args:
        query (str): Search query
        top_k (int): Number of top results to return

    Returns:
        list: Top k recipe objects as dictionaries
    """

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

    top_results = [RECIPES[index] for index in top_indices]

    return top_results

def search_wrapper(
    query: str,
    top_k: int = 5
)-> str:
    results = search(query, top_k)
    return json.dumps(results, indent=4)

with gr.Blocks() as demo:
    gr.api(search)
    with gr.Row():
        input_textbox = gr.Textbox(label="Query")
        topk_number = gr.Number(
            label="Top K",
            value=5,
            precision=0
        )
    with gr.Column():
        submit_button = gr.Button("Search")
        output_json = gr.JSON(label="Results")
    submit_button.click(
        search_wrapper,
        inputs=[input_textbox, topk_number],
        outputs=output_json
    )

demo.launch(
    share=True,
    mcp_server=True,
)
# ----------------------------------------------------------------------------------------------------