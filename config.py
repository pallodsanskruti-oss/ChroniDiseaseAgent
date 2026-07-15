"""
Application configuration — loads .env and exposes typed settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Flask ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("APP_PORT", 5000))

    # ── IBM Watsonx.ai ─────────────────────────────────────────────────────
    IBM_API_KEY: str = os.getenv("IBM_API_KEY", "")
    WATSONX_URL: str = os.getenv(
        "IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com"
    )
    WATSONX_PROJECT_ID: str = os.getenv("IBM_WATSONX_PROJECT_ID", "")

    # Granite model to use
    GRANITE_MODEL_ID: str = "ibm/granite-4-h-small"

    # Fallback: use a Deployment Space ID if project creation failed (503 error)
    # Leave blank if you have a valid WATSONX_PROJECT_ID
    WATSONX_SPACE_ID: str = os.getenv("IBM_WATSONX_SPACE_ID", "")

    # ── Watsonx generation parameters ─────────────────────────────────────
    MAX_NEW_TOKENS: int = 1024
    TEMPERATURE: float = 0.3
    TOP_P: float = 0.9
    REPETITION_PENALTY: float = 1.1
