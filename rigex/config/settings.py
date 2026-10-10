"""
ResolveAI Configuration Settings & Security Management.
Loads environment variables safely, defines deterministic business policies,
and verifies independent Gemini API keys and model readiness for Planner, Worker, and Reviewer.
"""

import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# General Fallback API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# 3 Dedicated Gemini API Keys (one for each role, with fallback to GEMINI_API_KEY)
PLANNER_API_KEY = (os.getenv("PLANNER_API_KEY") or GEMINI_API_KEY).strip()
WORKER_API_KEY = (os.getenv("WORKER_API_KEY") or GEMINI_API_KEY).strip()
REVIEWER_API_KEY = (os.getenv("REVIEWER_API_KEY") or GEMINI_API_KEY).strip()

# 3 Dedicated Gemini Models (Defaulting to 3 distinct supported models)
PLANNER_MODEL = os.getenv("PLANNER_MODEL", "gemini-3.5-flash").strip()
WORKER_MODEL = os.getenv("WORKER_MODEL", "gemini-3.8-flash").strip()
REVIEWER_MODEL = os.getenv("REVIEWER_MODEL", "gemini-2.5-flash").strip()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001").strip()

# Database & Storage
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SQLITE_DB_PATH = BASE_DIR / os.getenv("SQLITE_DB_PATH", "data/resolveai.db")
CHROMA_PERSIST_DIR = BASE_DIR / os.getenv("CHROMA_PERSIST_DIR", "data/chroma_db")
POLICIES_DIR = BASE_DIR / "rag" / "policies"

# Security & Admin
ADMIN_PIN = os.getenv("ADMIN_PIN", "1234")

# Deterministic Business Rules for Returns and Refunds
BUSINESS_RULES: Dict[str, Any] = {
    "return_window_days": 30,
    "instant_damaged_max_amount": 50.00,  # Below $50, instant refund without requiring item return
    "delayed_delivery_cancel_days": 14,   # Delayed > 14 days past ETA: 100% full cancellation refund
    "high_value_approval_threshold": 150.00,  # Refunds >= $150 require Admin human approval
    "missing_delivery_approval_threshold": 75.00, # Missing claim when carrier shows delivered >= $75 requires Admin approval
    "return_shipping_fee": 5.99,          # Standard deduction for change of mind
    "store_credit_bonus_pct": 10.0,       # 10% extra credit for store credit resolution
}

# Supported Gemini Model candidates for fallback / selection
SUPPORTED_GEMINI_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.8-flash",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]


def is_valid_key(key: str) -> bool:
    """Check if key is valid and not a placeholder."""
    clean = (key or "").strip()
    return bool(clean and clean != "replace_with_your_real_api_key" and len(clean) > 15)


def is_api_key_configured(role: Optional[str] = None) -> bool:
    """Check if API key is configured for a specific role or generally."""
    load_dotenv(BASE_DIR / ".env", override=True)
    if role == "planner":
        key = (os.getenv("PLANNER_API_KEY") or os.getenv("GEMINI_API_KEY", "")).strip()
    elif role == "worker":
        key = (os.getenv("WORKER_API_KEY") or os.getenv("GEMINI_API_KEY", "")).strip()
    elif role == "reviewer":
        key = (os.getenv("REVIEWER_API_KEY") or os.getenv("GEMINI_API_KEY", "")).strip()
    else:
        key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("PLANNER_API_KEY", "").strip()
    return is_valid_key(key)


def mask_key(key: str) -> str:
    """Format key into masked representation."""
    if not is_valid_key(key):
        return "Not Configured"
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]} ({len(key)} chars)"


def get_masked_api_key(role_or_key: Optional[str] = None) -> str:
    """Return safe masked representation of API key without exposing secret."""
    load_dotenv(BASE_DIR / ".env", override=True)
    if role_or_key == "planner":
        key = (os.getenv("PLANNER_API_KEY") or os.getenv("GEMINI_API_KEY", "")).strip()
    elif role_or_key == "worker":
        key = (os.getenv("WORKER_API_KEY") or os.getenv("GEMINI_API_KEY", "")).strip()
    elif role_or_key == "reviewer":
        key = (os.getenv("REVIEWER_API_KEY") or os.getenv("GEMINI_API_KEY", "")).strip()
    elif role_or_key and len(role_or_key) > 10 and not role_or_key.isalpha():
        key = role_or_key
    else:
        key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("PLANNER_API_KEY", "").strip()
    return mask_key(key)


def get_role_credentials(role: str) -> Dict[str, Any]:
    """Retrieve model ID and API key for a specific role."""
    load_dotenv(BASE_DIR / ".env", override=True)
    role_lower = role.lower()
    if role_lower == "planner":
        model = os.getenv("PLANNER_MODEL", "gemini-3.5-flash").strip()
        key = (os.getenv("PLANNER_API_KEY") or os.getenv("GEMINI_API_KEY", "")).strip()
    elif role_lower == "worker":
        model = os.getenv("WORKER_MODEL", "gemini-3.8-flash").strip()
        key = (os.getenv("WORKER_API_KEY") or os.getenv("GEMINI_API_KEY", "")).strip()
    elif role_lower == "reviewer":
        model = os.getenv("REVIEWER_MODEL", "gemini-2.5-flash").strip()
        key = (os.getenv("REVIEWER_API_KEY") or os.getenv("GEMINI_API_KEY", "")).strip()
    else:
        model = os.getenv("PLANNER_MODEL", "gemini-3.5-flash").strip()
        key = os.getenv("GEMINI_API_KEY", "").strip()

    return {
        "role": role,
        "model": model,
        "api_key": key,
        "masked_key": mask_key(key),
        "is_configured": is_valid_key(key)
    }


def save_role_configuration(
    planner_key: Optional[str] = None, planner_model: Optional[str] = None,
    worker_key: Optional[str] = None, worker_model: Optional[str] = None,
    reviewer_key: Optional[str] = None, reviewer_model: Optional[str] = None
) -> bool:
    """Save updated keys and models to .env file."""
    env_path = BASE_DIR / ".env"
    existing_vars = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    existing_vars[k.strip()] = v.strip()

    if planner_key is not None:
        existing_vars["PLANNER_API_KEY"] = planner_key.strip()
    if planner_model is not None:
        existing_vars["PLANNER_MODEL"] = planner_model.strip()

    if worker_key is not None:
        existing_vars["WORKER_API_KEY"] = worker_key.strip()
    if worker_model is not None:
        existing_vars["WORKER_MODEL"] = worker_model.strip()

    if reviewer_key is not None:
        existing_vars["REVIEWER_API_KEY"] = reviewer_key.strip()
    if reviewer_model is not None:
        existing_vars["REVIEWER_MODEL"] = reviewer_model.strip()

    with open(env_path, "w", encoding="utf-8") as f:
        f.write("# ResolveAI Multi-Agent Multi-Key Configuration\n")
        f.write("# 1. Planner Agent\n")
        f.write(f"PLANNER_API_KEY={existing_vars.get('PLANNER_API_KEY', '')}\n")
        f.write(f"PLANNER_MODEL={existing_vars.get('PLANNER_MODEL', 'gemini-3.5-flash')}\n\n")

        f.write("# 2. Worker Agent\n")
        f.write(f"WORKER_API_KEY={existing_vars.get('WORKER_API_KEY', '')}\n")
        f.write(f"WORKER_MODEL={existing_vars.get('WORKER_MODEL', 'gemini-3.8-flash')}\n\n")

        f.write("# 3. Reviewer Agent\n")
        f.write(f"REVIEWER_API_KEY={existing_vars.get('REVIEWER_API_KEY', '')}\n")
        f.write(f"REVIEWER_MODEL={existing_vars.get('REVIEWER_MODEL', 'gemini-2.5-flash')}\n\n")

        f.write("# Fallback / Embedding & Storage\n")
        f.write(f"GEMINI_API_KEY={existing_vars.get('GEMINI_API_KEY', existing_vars.get('PLANNER_API_KEY', ''))}\n")
        f.write(f"EMBEDDING_MODEL={existing_vars.get('EMBEDDING_MODEL', 'gemini-embedding-001')}\n")
        f.write(f"CHROMA_PERSIST_DIR={existing_vars.get('CHROMA_PERSIST_DIR', 'data/chroma_db')}\n")
        f.write(f"SQLITE_DB_PATH={existing_vars.get('SQLITE_DB_PATH', 'data/resolveai.db')}\n")
        f.write(f"APP_ENV={existing_vars.get('APP_ENV', 'development')}\n")
        f.write(f"ADMIN_PIN={existing_vars.get('ADMIN_PIN', '1234')}\n")

    load_dotenv(env_path, override=True)
    return True


def test_gemini_connection(model_id: Optional[str] = None, api_key: Optional[str] = None, role: Optional[str] = None) -> Tuple[bool, str]:
    """
    Directly verify connectivity to Google Gemini API using official google-genai SDK.
    Accepts specific role, model_id, or api_key.
    Returns (success: bool, status_message: str).
    """
    if role:
        creds = get_role_credentials(role)
        target_model = model_id or creds["model"]
        target_key = api_key or creds["api_key"]
    else:
        target_model = model_id or os.getenv("PLANNER_MODEL", "gemini-3.5-flash")
        target_key = api_key or os.getenv("PLANNER_API_KEY") or os.getenv("GEMINI_API_KEY", "")

    target_key = (target_key or "").strip()
    if not is_valid_key(target_key):
        return False, f"API key for model '{target_model}' is not configured or contains placeholder value."

    try:
        from google import genai
        client = genai.Client(api_key=target_key)
        response = client.models.generate_content(
            model=target_model,
            contents="Respond with the single word: OK"
        )
        if response and response.text:
            return True, f"Connection verified successfully on model '{target_model}'."
        return False, f"Model '{target_model}' returned empty response."
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg or "resource_exhausted" in err_msg.lower() or "quota" in err_msg.lower():
            return False, f"Quota Exceeded (429 RESOURCE_EXHAUSTED). The Gemini API key has exceeded its rate or daily quota limit. ResolveAI gracefully operates in Deterministic Demo Mode."
        if "404" in err_msg or "not found" in err_msg.lower():
            return False, f"Model '{target_model}' is not available or deprecated on this API key. Try switching to gemini-2.5-flash, gemini-3.5-flash, or gemini-3.8-flash."
        if "403" in err_msg or "permission" in err_msg.lower() or "api_key" in err_msg.lower():
            return False, f"Authentication failed: Invalid API key or permission issue ({err_msg[:100]})."
        return False, f"Gemini API connection error: {err_msg[:120]}"
