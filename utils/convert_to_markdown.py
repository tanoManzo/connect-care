# ----------------------------------------------------------------------------------------------------
# Script to convert recipe files to Markdown format.
# PDF files are converted directly, TXT files should contain URLs to fetch.
# ----------------------------------------------------------------------------------------------------
import io
import time
import argparse
import requests
# ----------------------------------------------------------------------------------------------------
from pathlib import Path
from tqdm.auto import tqdm
from markitdown import MarkItDown, StreamInfo
# ----------------------------------------------------------------------------------------------------
# Global markitdown instance
MARKITDOWN = MarkItDown()
# ----------------------------------------------------------------------------------------------------
def convert_file(
    file_path,
    delay,
):
    """Convert a single file to Markdown format.

    PDFs are converted directly, TXT files should contain a URL to fetch.
    """
    try:
        # Determine output markdown file path
        output_md_file_path = file_path.with_suffix(".md")

        match file_path.suffix:
            case ".pdf":
                # Convert PDF directly using markitdown
                result = MARKITDOWN.convert(str(file_path))
                markdown_content = result.text_content

            case ".txt":
                # TXT files contain URLs to fetch and convert
                with open(file_path, "r", encoding="utf-8") as url_file:
                    content = url_file.read().strip()

                # Add delay to avoid rate limiting
                time.sleep(delay)

                # Fetch the URL content
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                response = requests.get(content, headers=headers)
                response.raise_for_status()

                # Convert HTML response to Markdown
                stream = io.BytesIO(response.content)
                result = MARKITDOWN.convert(
                    stream, stream_info=StreamInfo(extension=".html")
                )
                markdown_content = result.text_content

            case _:
                raise ValueError(f"Unknown file type: {file_path.suffix}")

        # Write Markdown output to file
        with open(output_md_file_path, "w", encoding="utf-8") as output_md_file:
            output_md_file.write(markdown_content)

        return True

    except Exception as e:
        print(f"Failed to convert {file_path}: {e}")
        return False
# ----------------------------------------------------------------------------------------------------
def main():
    """Main entry point for the script."""
    # Setup command line argument parser
    parser = argparse.ArgumentParser(
        description="Convert recipe files to Markdown. PDFs are converted directly, TXT files should contain URLs to fetch."
    )
    parser.add_argument(
        "--recipe-dir",
        type=str,
        default="data/recipes",
        help="Path to the recipe directory (default: data/recipes)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=5,
        help="Delay in seconds between URL requests (default: 5)",
    )
    args = parser.parse_args()

    # Validate recipe directory
    recipe_directory = Path(args.recipe_dir)
    if not recipe_directory.exists():
        print(f"Recipe directory not found: {recipe_directory}")
        return

    # Find all PDF and TXT files recursively
    pdf_files = list(recipe_directory.rglob("*.pdf"))
    txt_files = list(recipe_directory.rglob("*.txt"))

    total_files = len(pdf_files) + len(txt_files)
    print(f"Found {total_files} recipe files to convert:")
    print(f"\t- PDF files: {len(pdf_files)}")
    print(f"\t- TXT files: {len(txt_files)}")

    if total_files == 0:
        print("No files found to convert!")
        return

    # Convert all files and track results
    success_count = 0
    failure_count = 0
    for file_path in tqdm(pdf_files + txt_files):
        if convert_file(file_path, delay=args.delay):
            success_count += 1
        else:
            failure_count += 1

    # Print final summary
    print(f"Conversion complete:")
    print(f"\t- Success: {success_count}")
    print(f"\t- Failed: {failure_count}")
    print(f"\t- Total: {total_files}")
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
# ----------------------------------------------------------------------------------------------------
