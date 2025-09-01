"""S3 upload and PDF-to-HTML conversion via ConvertAPI."""

import os
import tempfile
from typing import List

import boto3
import certifi
import convertapi
import requests

from ..core.config import get_settings


def upload_papers_to_s3(uid: str, search_query: str, papers: list) -> None:
    """Upload paper PDFs from open-access URLs to S3."""
    settings = get_settings()
    settings.configure_aws_env()

    s3 = boto3.client("s3")
    s3_prefix = f"{uid}/{search_query}/"
    session = requests.Session()
    session.verify = certifi.where()

    for paper in papers:
        try:
            if not paper.get("openAccessPdf"):
                continue
            response = session.get(paper["openAccessPdf"]["url"], stream=True)
            if response.status_code != 200:
                continue
            pdf_name = paper["title"] + ".pdf"
            s3.upload_fileobj(
                response.raw,
                settings.s3_bucket,
                f"{s3_prefix}{pdf_name}",
            )
        except (requests.RequestException, OSError):
            continue


def convert_pdf_to_html(pdf_name: str, pdf_path: str, html_path: str) -> None:
    """Convert a PDF to HTML using ConvertAPI."""
    settings = get_settings()
    convertapi.api_credentials = settings.convertapi_credentials

    os.makedirs(html_path, exist_ok=True)
    convertapi.convert(
        "html", {"File": pdf_path, "Wysiwyg": "false"}, from_format="pdf"
    ).save_files(f"{html_path}/{pdf_name}.html")


def read_pdfs_from_s3(
    uid: str, search_query: str, html_output_path: str
) -> List[str]:
    """Download PDFs from S3, convert to HTML, return list of paper titles."""
    settings = get_settings()
    settings.configure_aws_env()

    s3 = boto3.client("s3")
    s3_prefix = f"{uid}/{search_query}/"
    response = s3.list_objects_v2(Bucket=settings.s3_bucket, Prefix=s3_prefix)

    if "Contents" not in response:
        return []

    with tempfile.TemporaryDirectory() as temp_dir:
        downloaded = []
        for item in response["Contents"]:
            key = item["Key"]
            local_path = os.path.join(temp_dir, key.split("/")[-1])
            try:
                with open(local_path, "wb") as f:
                    s3.download_fileobj(settings.s3_bucket, key, f)
                downloaded.append(local_path)
            except OSError:
                continue

        successful = []
        for pdf_path in downloaded:
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            try:
                convert_pdf_to_html(pdf_name, pdf_path, html_output_path)
                successful.append(pdf_name)
            except Exception:
                continue
        return successful
