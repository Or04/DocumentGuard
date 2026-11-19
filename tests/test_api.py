import io, json
from docx import Document
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
KEY = 'sk-test-local-fake-not-real-1234567'

def doc():
    document = Document()
    document.add_paragraph('Detection range is 50 km.')
    output = io.BytesIO()
    document.save(output)
    return output.getvalue()

def post(content=None, name='test.docx', rules=None, key=KEY):
    fields = {'rules': json.dumps(rules if rules is not None else ['Flag numerical detection range']), 'api_key': key}
    if key is None:
        del fields['api_key']
    return client.post('/api/analyze', files={'file': (name, content if content is not None else doc(), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}, data=fields)

def test_home():
    response = client.get('/')
    assert response.status_code == 200
    assert 'Connect key' in response.text
    assert 'no-store' in response.headers['cache-control']

def test_health():
    assert client.get('/health').json()['auth'] == 'bring-your-own-key'

def test_missing_key():
    assert post(key=None).status_code == 422

def test_invalid_key():
    assert post(key='bad').status_code == 400

def test_key_not_echoed_in_error(monkeypatch):
    from app import main
    monkeypatch.setattr(main, 'analyze', lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError('provider secret ' + KEY)))
    response = post()
    assert response.status_code == 502
    assert KEY not in response.text
    assert 'provider secret' not in response.text

def test_request_key_is_passed_only_to_provider(monkeypatch):
    from app import main
    received = {}
    def fake_analyze(blocks, rules, api_key):
        received.update(api_key=api_key, blocks=blocks, rules=rules)
        return {'count': 0, 'violations': [], 'rejected_unverified': 0, 'blocks_scanned': len(blocks), 'rules_scanned': len(rules), 'engine': 'mock-semantic'}
    monkeypatch.setattr(main, 'analyze', fake_analyze)
    response = post()
    assert response.status_code == 200
    assert received['api_key'] == KEY
    assert KEY not in response.text

def test_wrong_extension():
    assert post(name='evil.txt').status_code == 400

def test_malformed_zip():
    assert post(content=b'broken').status_code == 400

def test_invalid_rules():
    assert post(rules=[]).status_code == 400

def test_oversized_document():
    assert post(content=b'x' * (5 * 1024 * 1024 + 1)).status_code == 400
