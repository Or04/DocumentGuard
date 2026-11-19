"""Browser → real FastAPI multipart route → parser → grounded AI flow (provider mocked)."""
import json
import sys
from types import SimpleNamespace
import os
from pathlib import Path

from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright
from docx import Document

from app.main import app


def test_real_browser_real_backend_mocked_provider(monkeypatch, tmp_path):
    from app import core

    secret = 'sk-integration-fake-key-not-real-abcdef'
    received = []

    class FakeOpenAI:
        def __init__(self, api_key, **kwargs):
            received.append(api_key)

    def fake_model_json(client, system_prompt, payload):
        if 'blocks' in payload:
            return {'findings': [{'rule_id': 'R1', 'block_id': 'p1', 'quote': 'Detection range is 50 km.', 'explanation': 'Numeric capability'}]}
        return {'decision': 'confirmed', 'reason': 'A numerical performance disclosure'}

    monkeypatch.setitem(sys.modules, 'openai', SimpleNamespace(OpenAI=FakeOpenAI))
    monkeypatch.setattr(core, 'model_json', fake_model_json)

    file = tmp_path / 'sensor.docx'
    doc = Document()
    doc.add_paragraph('Detection range is 50 km.')
    doc.save(file)
    html = (Path(__file__).resolve().parents[1] / 'app' / 'static' / 'index.html').read_text()
    backend = TestClient(app)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=os.getenv('CHROMIUM_PATH') or None, args=['--no-sandbox'])
        page = browser.new_page()
        page.set_content(html, wait_until='load')
        # An origin-less page cannot fetch a relative path. Route to a fake HTTPS
        # origin, then forward the exact multipart bytes to the real FastAPI app.
        page.evaluate("""() => { const original = window.fetch.bind(window); window.fetch = (path, opts) => original('https://documentguard.test' + path, opts); }""")

        requests = []
        def forward(route):
            request = route.request
            requests.append(request)
            # Playwright omits multipart File bytes in intercepted post_data_buffer.
            # Reinsert the already selected test DOCX; the remaining multipart fields
            # (including the user-supplied API key and rules) are forwarded intact.
            raw = request.post_data_buffer
            content_type = b'Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document\r\n\r\n'
            assert content_type + b'\r\n--' in raw
            body = raw.replace(content_type + b'\r\n--', content_type + file.read_bytes() + b'\r\n--', 1)
            response = backend.post('/api/analyze', content=body, headers={'content-type': request.headers['content-type']})
            route.fulfill(status=response.status_code, headers={'content-type': 'application/json', 'access-control-allow-origin': '*'}, body=response.text)

        page.route('https://documentguard.test/api/analyze', forward)
        page.locator('#file').set_input_files(str(file))
        page.locator('#connect').click()
        page.locator('#key-input').fill(secret)
        page.locator('#key-save').click()
        page.locator('#run').click()
        page.locator('.violation').wait_for(timeout=10000)
        assert '50 km' in page.locator('.quote').inner_text()
        assert 'Evidence verified' in page.locator('.verified').inner_text()
        assert received == [secret]
        assert len(requests) == 1
        assert secret not in page.locator('body').inner_text()
        browser.close()
