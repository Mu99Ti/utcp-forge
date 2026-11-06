#!/usr/bin/env python3
"""Standalone runner script for the utcp-forge skill."""
import sys
from pathlib import Path

# Add src to sys.path
# File path: <repo>/skills/utcp-forge/scripts/run_forge.py
# parent -> scripts
# parent.parent -> utcp-forge
# parent.parent.parent -> skills
# parent.parent.parent.parent -> <repo>
root_dir = Path(__file__).resolve().parent.parent.parent.parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from utcp_forge.cli import app

if __name__ == "__main__":
    app()
