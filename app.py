"""Vercel entrypoint.

Vercel imports this file under the module name `app`, which otherwise shadows
our `app/` package. Give the entrypoint the package search path before importing
our FastAPI application; this keeps the existing package layout intact.
"""
from pathlib import Path

__path__ = [str(Path(__file__).resolve().parent / 'app')]
from app.main import app
