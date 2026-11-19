"""Agent skill CLI. Pass the key by process environment, never CLI args."""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from app.core import analyze, parse_docx, validate_rules

parser = argparse.ArgumentParser(description='DocumentGuard DOCX compliance review')
parser.add_argument('--file', required=True)
parser.add_argument('--rule', required=True, action='append')
args = parser.parse_args()

try:
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        raise ValueError('Set OPENAI_API_KEY in your local process environment; do not commit it')
    result = analyze(parse_docx(Path(args.file).read_bytes()), validate_rules(args.rule), api_key=key)
    print(json.dumps(result, ensure_ascii=False, indent=2))
except Exception:
    # Do not expose provider errors or user document content on stderr.
    print('Review failed. Verify inputs and provider credentials.', file=sys.stderr)
    sys.exit(2)
