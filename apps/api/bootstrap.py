import os
from dotenv import load_dotenv

# Load .env file if present (local development). Render environment variables take precedence.
load_dotenv()

# Disable GPU/CUDA for safety on Render free tier
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

# Make HuggingFace/Transformers quieter & lighter
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

