"""Application configuration from environment variables.

All secrets and config are loaded from env. Create a .env file with required keys.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv

    for p in [
        Path(__file__).resolve().parent.parent.parent / ".env",
        Path(__file__).resolve().parent.parent.parent.parent / ".env",
    ]:
        if p.exists():
            load_dotenv(p)
            break
    else:
        load_dotenv()
except ImportError:
    pass


def _get(key: str, default: Optional[str] = None) -> str:
    value = os.getenv(key, default or "")
    if not value and default is None:
        raise ValueError(
            f"Missing required environment variable: {key}. "
            "Set it in your environment or .env file."
        )
    return value


@lru_cache(maxsize=1)
def get_settings() -> "Settings":
    return Settings()


class Settings:
    """App settings from environment variables."""

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "")
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        self.aws_region = os.getenv("AWS_DEFAULT_REGION", "us-east-2")
        self.s3_bucket = os.getenv("S3_BUCKET", "paper-full-texts")
        self.convertapi_credentials = os.getenv("CONVERTAPI_CREDENTIALS", "")
        self.semanticscholar_api_key = os.getenv("SEMANTICSCHOLAR_API_KEY", "")
        self.pdf_base_path = Path(
            os.getenv(
                "PDF_BASE_PATH",
                str(Path(__file__).resolve().parent.parent / "pdf_parsing"),
            )
        )

    def configure_aws_env(self) -> None:
        """Set AWS env vars for boto3 (if credentials are configured)."""
        if self.aws_access_key_id:
            os.environ["AWS_ACCESS_KEY_ID"] = self.aws_access_key_id
        if self.aws_secret_access_key:
            os.environ["AWS_SECRET_ACCESS_KEY"] = self.aws_secret_access_key
        if self.aws_region:
            os.environ["AWS_DEFAULT_REGION"] = self.aws_region
