"""Regression checks for accidental BYOK disclosure at the application boundary.

These tests do not prove Vercel/CDN/APM infrastructure redaction.
"""
import io
import logging
import json

from docx import Document
from fastapi.testclient import TestClient
from app.main import app

CANARY = "sk-test-canary-never-real-avoid-log-leak-987654321"
client = TestClient(app)


def _docx():
    doc = Document()
    doc.add_paragraph("Detection range is 50 km.")
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def test_request_scoped_key_is_not_logged_or_returned(monkeypatch, caplog):
    from app import main

    observed = {}

    def fake_analyze(blocks, rules, api_key):
        observed["key"] = api_key
        return {
            "engine": "mock",
            "violations": [],
            "count": 0,
            "rejected_unverified": 0,
            "blocks_scanned": len(blocks),
            "rules_scanned": len(rules),
        }

    monkeypatch.setattr(main, "analyze", fake_analyze)
    with caplog.at_level(logging.DEBUG):
        response = client.post(
            "/api/analyze",
            data={"rules": json.dumps(["Flag numerical detection range"])},
            files={"file": ("sample.docx", _docx())},
            headers={"Authorization": "Bearer " + CANARY},
        )
    assert response.status_code == 200
    assert observed["key"] == CANARY
    assert CANARY not in response.text
    assert CANARY not in caplog.text
    assert response.headers["cache-control"] == "no-store, private"


def test_provider_exception_does_not_expose_key(monkeypatch, caplog):
    from app import main

    def fail(*args, **kwargs):
        raise RuntimeError("Provider error contained secret " + CANARY)

    monkeypatch.setattr(main, "analyze", fail)
    with caplog.at_level(logging.DEBUG):
        response = client.post(
            "/api/analyze",
            data={"rules": json.dumps(["Flag numerical detection range"])},
            files={"file": ("sample.docx", _docx())},
            headers={"Authorization": "Bearer " + CANARY},
        )
    assert response.status_code == 502
    assert CANARY not in response.text
    assert CANARY not in caplog.text
    assert "Provider error contained secret" not in response.text


def test_multipart_key_is_not_accepted():
    response = client.post(
        "/api/analyze",
        data={
            "rules": json.dumps(["Flag numerical detection range"]),
            "api_key": CANARY,
        },
        files={"file": ("sample.docx", _docx())},
    )
    assert response.status_code == 400
    assert CANARY not in response.text
