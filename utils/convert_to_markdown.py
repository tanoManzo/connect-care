# ----------------------------------------------------------------------------------------------------
import io
import time
import requests
# ----------------------------------------------------------------------------------------------------
from pathlib import Path
from tqdm.auto import tqdm
from markitdown import MarkItDown, StreamInfo
# ----------------------------------------------------------------------------------------------------
MARKITDOWN = MarkItDown()
# ----------------------------------------------------------------------------------------------------
def convert_file(file_path):
    try:
        output_md_file_path = file_path.with_suffix(".md")
        match file_path.suffix:
            case ".pdf":
                result = MARKITDOWN.convert(str(file_path))
                markdown_content = result.text_content
            case ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                time.sleep(5)
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                response = requests.get(content, headers=headers)
                response.raise_for_status()
                stream = io.BytesIO(response.content)
                result = MARKITDOWN.convert(
                    stream, stream_info=StreamInfo(extension=".html")
                )
                markdown_content = result.text_content
            case _:
                raise ValueError(f"Unknown file type: {file_path.suffix}")
        with open(output_md_file_path, "w", encoding="utf-8") as output_md_file:
            output_md_file.write(markdown_content)
        return True
    except Exception as e:
        print(f"Failed to convert {file_path}: {e}")
        return False
# ----------------------------------------------------------------------------------------------------
def main():
    recipe_directory = Path("data/recipes")
    if not recipe_directory.exists():
        print(f"Recipe directory not found: {recipe_directory}")
        return

    pdf_files = list(recipe_directory.rglob("*.pdf"))
    txt_files = list(recipe_directory.rglob("*.txt"))

    total_files = len(pdf_files) + len(txt_files)
    print(f"Found {total_files} recipe files to convert:")
    print(f"\t- PDF files: {len(pdf_files)}")
    print(f"\t- TXT files: {len(txt_files)}")

    if total_files == 0:
        print("No files found to convert!")
        return

    success_count = 0
    failure_count = 0

    for file_path in tqdm(pdf_files + txt_files):
        if convert_file(file_path):
            success_count += 1
        else:
            failure_count += 1
    print(f"Conversion complete:")
    print(f"\t- Success: {success_count}")
    print(f"\t- Failed: {failure_count}")
    print(f"\t- Total: {total_files}")
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------------------------------