import os
from docx import Document


def extract_headings_with_content(docx_path):
    doc = Document(docx_path)
    headings_with_content = {}
    current_heading = None

    for paragraph in doc.paragraphs:
        if paragraph.style.name.startswith("Heading"):
            current_heading = paragraph.text
            headings_with_content[current_heading] = []
        elif current_heading:
            headings_with_content[current_heading].append(paragraph.text)

    return headings_with_content


def save_to_markdown(headings_with_content, markdown_path):
    with open(markdown_path, "w") as md_file:
        for heading, content in headings_with_content.items():
            md_file.write(f"## {heading}\n\n")
            for line in content:
                md_file.write(f"{line}\n\n")
            md_file.write("\n---\n\n")  # Separator between sections


def convert_folder_docx_to_md(docx_folder, md_folder):
    if not os.path.exists(md_folder):
        os.makedirs(md_folder)

    for filename in os.listdir(docx_folder):
        if filename.endswith(".docx"):
            docx_path = os.path.join(docx_folder, filename)
            markdown_filename = f"{os.path.splitext(filename)[0]}.md"
            markdown_path = os.path.join(md_folder, markdown_filename)

            headings_with_content = extract_headings_with_content(docx_path)
            save_to_markdown(headings_with_content, markdown_path)


# Paths for input folder and output folder
# docx_folder = "/Users/rajamuhammedomar/latest-fyr/ForYourResearch/backend/app/pdf_parsing/naman_split_docxs"
# md_folder = "./naman_new"

# convert_folder_docx_to_md(docx_folder, md_folder)
