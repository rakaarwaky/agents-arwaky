"""Pytest fixtures for BlenderMCP test suite."""
import sys
import os

# Ensure src/ is on sys.path for test imports
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
