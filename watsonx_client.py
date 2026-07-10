"""
Watsonx.ai integration — wraps IBM ibm-watsonx-ai SDK.
"""
from __future__ import annotations
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
from config import Config


def _get_model() -> ModelInference:
    credentials = Credentials(
        url=Config.WATSONX_URL,
        api_key=Config.IBM_API_KEY,
    )
    client = APIClient(credentials)

    # Use space_id if project_id is not available (project creation failed).
    # Set WATSONX_SPACE_ID in .env as a fallback.
    project_id = Config.WATSONX_PROJECT_ID or None
    space_id   = Config.WATSONX_SPACE_ID   or None

    return ModelInference(
        model_id=Config.GRANITE_MODEL_ID,
        api_client=client,
        project_id=project_id if project_id else None,
        space_id=space_id     if not project_id else None,
        params={
            GenParams.MAX_NEW_TOKENS:      Config.MAX_NEW_TOKENS,
            GenParams.TEMPERATURE:         Config.TEMPERATURE,
            GenParams.TOP_P:               Config.TOP_P,
            GenParams.REPETITION_PENALTY:  Config.REPETITION_PENALTY,
        },
    )


def query_watsonx(system_prompt: str, user_message: str) -> str:
    """
    Send a chat message to Granite via Watsonx.ai and return the response text.
    Falls back to a descriptive error string so the UI never crashes.
    """
    try:
        model = _get_model()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ]
        response = model.chat(messages=messages)
        return response["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        return (
            f"[ERROR] Watsonx.ai connection error: {exc}\n\n"
            "Please verify your IBM_API_KEY and IBM_WATSONX_PROJECT_ID in the .env file, "
            "then restart the application."
        )
