import sys
import os
from pathlib import Path

# Signal Vercel serverless environment
os.environ["VERCEL"] = "1"

# Add project root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
