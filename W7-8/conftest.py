import sys
from pathlib import Path

# Ensure project root is in sys.path during pytest discovery and execution
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
