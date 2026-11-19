"""Real Chromium browser journey. Uses a routed AI response; never needs a real key."""
import json, os
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

SAMPLE = {
    'count': 1, 'blocks_scanned': 1, 'rules_scanned': 1,
    'engine': 'semantic-ai-with-evidence-and-independent-review',
    'violations': [{'rule_id': 'R1', 'rule': 'Flag disclosures of numeric operational performance.',
                    'quote': 'Detection range is 50 km.', 'explanation': 'Performance capability',
                    'location': 'Paragraph 1', 'status': 'evidence_verified'}]
}


def test_byok_upload_review_export(tmp_path):
    from docx import Document
    doc = Document()
    doc.add_paragraph('Detection range is 50 km.')
    sample_path = tmp_path / 'sample.docx'
    doc.save(sample_path)
    html = Path(__file__).resolve().parents[1] / 'app' / 'static' / 'index.html'
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=os.getenv('CHROMIUM_PATH') or None, args=['--no-sandbox'])
        page = browser.new_page(accept_downloads=True)
        # set_content works in locked-down runners that block navigating to localhost;
        # GitHub CI additionally serves the same file from FastAPI.
        if os.getenv('E2E_BASE_URL'):
            page.goto(os.environ['E2E_BASE_URL'])
        else:
            page.set_content(html.read_text(), wait_until='load')
        assert 'not connected' in page.locator('#key-state').inner_text()
        assert page.locator('#key-input').input_value() == ''
        requests = []
        def intercept(route):
            body = route.request.post_data or ''
            requests.append((body, route.request.headers.get('authorization', '')))
            route.fulfill(status=200, content_type='application/json', body=json.dumps(SAMPLE))
        if os.getenv('E2E_BASE_URL'):
            page.route('**/api/analyze', intercept)
        else:
            # about:blank has no URL origin; intercept fetch at the browser API boundary.
            page.evaluate('''(sample) => { window.__captured = []; window.fetch = async (url, options) => { window.__captured.push({fields:Array.from(options.body.entries()).map(([key,value]) => [key, value instanceof File ? value.name : value]),authorization:options.headers.Authorization}); return new Response(JSON.stringify(sample), {status:200,headers:{'Content-Type':'application/json'}}); }; }''', SAMPLE)
        page.locator('#file').set_input_files(str(sample_path))
        page.locator('#run').click()
        assert 'Connect your OpenAI API key' in page.locator('#status').inner_text()
        page.locator('#connect').click()
        page.locator('#key-input').fill('sk-fake-e2e-credential-not-real-12345678')
        page.locator('#key-save').click()
        assert page.locator('#key-modal').is_hidden()
        assert page.locator('#key-input').input_value() == ''
        assert 'connected' in page.locator('#key-state').inner_text()
        assert not page.locator('body').inner_text().find('sk-fake-e2e') >= 0
        page.locator('#run').click()
        page.locator('.violation').wait_for(timeout=15000)
        assert '50 km' in page.locator('.quote').inner_text()
        if os.getenv('E2E_BASE_URL'):
            assert len(requests) == 1
            assert 'sk-fake-e2e' not in requests[0][0]
            assert requests[0][1].startswith('Bearer sk-fake-e2e')
        else:
            captured = page.evaluate('window.__captured')
            assert len(captured) == 1
            assert all(key != 'api_key' for key,value in captured[0]['fields'])
            assert captured[0]['authorization'].startswith('Bearer sk-fake-e2e')
        assert 'Detection range is 50 km.' not in page.locator('#status').inner_text()
        with page.expect_download() as download:
            page.locator('#export').click()
        assert download.value.suggested_filename == 'documentguard-report.json'
        page.locator('#connect').click()  # disconnect before optionally replacing
        page.locator('#key-cancel').click()
        assert 'not connected' in page.locator('#key-state').inner_text()
        browser.close()
