import re
from docx import Document
from shutil import copyfile
import os


def split_merged_docx_with_formatting(input_docx_path, output_dir, paper_titles):
    os.makedirs(output_dir, exist_ok=True)

    # Load the merged DOCX file
    doc = Document(input_docx_path)
    sections = []
    current_section = []

    # Regex pattern to identify the separator text
    pattern = re.compile(r"Start of PDF Naman_Omar (\d+)")

    # Iterate through paragraphs in the document
    for paragraph in doc.paragraphs:
        # Check if the paragraph matches the separator pattern
        match = pattern.match(paragraph.text)

        # When a match is found, start a new section
        if match:
            # Save the current section if it contains paragraphs
            if current_section:
                sections.append(current_section)
                current_section = []

        # Append the paragraph (along with its formatting) to the current section
        current_section.append(paragraph)

    # Append the last section if it exists
    if current_section:
        sections.append(current_section)

    # Process each section and its corresponding title
    for i, section in enumerate(sections):
        # Check if a title exists for this section
        if i < len(paper_titles):
            title = paper_titles[i]
        else:
            continue

        # Create a new document for the section
        output_doc = Document()

        for paragraph in section:
            # Add each paragraph with its formatting to the new document
            new_paragraph = output_doc.add_paragraph(paragraph.text)
            new_paragraph.style = paragraph.style  # Retain the paragraph's style

        output_path = f"{output_dir}/{title}.docx"
        output_doc.save(output_path)


# Example usage:
# input_docx_path = '/Users/rajamuhammedomar/latest-fyr/ForYourResearch/backend/app/pdf_parsing/merged_docxs/2eYbiBc5shN2ynLx857epU9BOH13/"naman"/123 - naman.docx'
# output_dir = "./naman_split_docxs"
# split_merged_docx_with_formatting(input_docx_path, output_dir, [1,2,3,4,5,6])
