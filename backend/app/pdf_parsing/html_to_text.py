from bs4 import BeautifulSoup
# from langchain_experimental.text_splitter import SemanticChunker
# from langchain_openai.embeddings import OpenAIEmbeddings
import os


def process_html_files(html_folder: str, paper_titles: list = None):
    # Ensure the folder exists; create it if it doesn't
    os.makedirs(html_folder, exist_ok=True)

    results = []

    for filename in os.listdir(html_folder):
        if filename.endswith(".html"):
            file_path = os.path.join(html_folder, filename)

            # Read content of the html file
            with open(file_path, "r") as html_file:
                content = html_file.read()
                results.append(
                    {"title": filename, "full_text": convert_html_to_txt(content)}
                )

    return results


def convert_html_to_txt(html: str) -> str:
    """Extract plain text from HTML content."""
    soup = BeautifulSoup(html, features="html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return "\n".join(chunk for chunk in chunks if chunk)
