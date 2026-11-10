import json
import math
import os
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

import gradio as gr

PROJECT_DIR = Path(__file__).resolve().parent
AI_SEARCH_SCRIPT = PROJECT_DIR / "AI_search.sh"
USER_API_ADDRESS = os.getenv("USER_API_ADDRESS", "http://127.0.0.1:8000")


def load_user_ids():
    query = urllib.parse.urlencode({"limit": 1000})
    request = urllib.request.Request(
        f"{USER_API_ADDRESS}/api/overview/high-risk-users?{query}"
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        rows = json.load(response)
    return [str(row["user_id"]) for row in rows if row.get("user_id")]


def recipes_to_markdown(recipes):
    sections = []
    for index, recipe in enumerate(recipes or [], start=1):
        lines = [f"## {index}. {recipe.get('title', 'Untitled recipe')}"]
        if recipe.get("servings"):
            lines.append(f"**Servings:** {recipe['servings']}")

        lines.append("")
        for section in recipe.get("ingredient_sections") or []:
            if section.get("section_name"):
                lines.append(f"**{section['section_name']}**")
            for ingredient in section.get("ingredients") or []:
                quantity = ingredient.get("quantity")
                name = ingredient.get("name", "ingredient")
                lines.append(f"- {quantity} {name}" if quantity else f"- {name}")

        if recipe.get("preparation"):
            lines.extend(["### Preparation", recipe["preparation"]])
        if recipe.get("preparation_time"):
            lines.append(f"**Preparation time:** {recipe['preparation_time']}")
        if recipe.get("notes"):
            lines.extend(["### Notes", recipe["notes"]])
        sections.append("\n".join(lines))

    return "\n\n---\n\n".join(sections) or "No recipes found."


def recommend(user_id: str, query: str, output_language: str = "en", top_k: int = 3) -> dict:
    if not user_id:
        raise gr.Error("Select a user ID.")
    if not query or not query.strip():
        raise gr.Error("Enter a recipe request.")
    if not output_language:
        output_language = "en"
    if (
        isinstance(top_k, bool)
        or not isinstance(top_k, (int, float))
        or (isinstance(top_k, float) and not math.isfinite(top_k))
        or top_k <= 0
        or int(top_k) != top_k
    ):
        raise gr.Error("top_k must be a positive integer.")
    top_k = int(top_k)

    environment = os.environ.copy()
    environment["USER_ID"] = user_id
    environment["QUERY"] = query.strip()
    environment["OUTPUT_LANGUAGE"] = output_language
    environment["TOP_K"] = str(top_k)

    result = subprocess.run(
        ["bash", str(AI_SEARCH_SCRIPT)],
        cwd=PROJECT_DIR,
        env=environment,
        capture_output=True,
        text=True,
        timeout=180,
    )

    if result.returncode != 0:
        error = result.stderr.strip() or result.stdout.strip() or "AI_search.sh failed."
        raise gr.Error(error[-2000:])

    try:
        recommendation = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise gr.Error(f"AI_search.sh returned invalid JSON: {error}") from error

    updated_recipes = recommendation.get("updated_recipes")
    if not updated_recipes:
        raise gr.Error("AI_search.sh did not return updated_recipes.")

    recommendation["recipe"] = recommendation["recipes"][0]
    recommendation["updated_recipe"] = updated_recipes[0]
    return recommendation


def run_recipe_search(user_id, query, output_language="en", top_k=3):
    recommendation = recommend(user_id, query, output_language, top_k)
    return (
        recipes_to_markdown(recommendation.get("recipes")),
        recipes_to_markdown(recommendation["updated_recipes"]),
        recommendation,
    )


def refresh_user_ids():
    try:
        user_ids = load_user_ids()
    except (OSError, ValueError):
        user_ids = ["user_001"]

    dropdown = gr.Dropdown(
        choices=user_ids,
        value=user_ids[0] if user_ids else None,
    )
    return dropdown, gr.Button(interactive=bool(user_ids))


with gr.Blocks(title="Connect Care Recipe Recommendations") as demo:
    gr.api(recommend, api_name="run_recipe_search")
    gr.Markdown("# Personalized recipe recommendation")
    gr.Markdown("Select a user and describe the recipe you want. The result keeps the original recipe and adds an adapted `updated_recipe`.")

    with gr.Row():
        user_id = gr.Dropdown(
            label="User ID",
            choices=[],
            value=None,
            allow_custom_value=True,
            scale=1,
        )
        output_language = gr.Dropdown(
            label="Updated recipe language",
            choices=["en", "es", "ca", "da"],
            value="en",
            scale=1,
        )
        top_k = gr.Number(
            label="Top K",
            value=3,
            minimum=1,
            precision=0,
            step=1,
            scale=1,
        )
        query = gr.Textbox(
            label="Recipe request",
            value="apple dessert for 2 people, no honey",
            placeholder="For example: a high-protein dinner without added sugar",
            scale=3,
        )

    search = gr.Button("Recommend recipe", variant="primary", interactive=False)

    with gr.Row():
        original_output = gr.Markdown(label="Original recipes", value="Select a user and run a search.")
        updated_output = gr.Markdown(label="Updated recipes", value="Select a user and run a search.")

    full_output = gr.JSON(label="Full response", show_label=True)

    demo.load(refresh_user_ids, outputs=[user_id, search], api_name="refresh_user_ids_ui")
    search.click(
        run_recipe_search,
        inputs=[user_id, query, output_language, top_k],
        outputs=[original_output, updated_output, full_output],
        api_name="run_recipe_search_ui",
    )


if __name__ == "__main__":
    server_port = int(os.getenv("GRADIO_SERVER_PORT", "7862"))
    demo.launch(server_name="0.0.0.0", server_port=server_port, share=True)
