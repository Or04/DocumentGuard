import io
import pytest
from docx import Document
from app.core import parse_docx,validate_rules,validate_findings,analyze

def make_doc(text='The maximum detection range is 50 km.'):
    d=Document();d.add_paragraph(text);b=io.BytesIO();d.save(b);return b.getvalue()
def test_parse():
    b=parse_docx(make_doc());assert b[0].id=='p1' and '50 km' in b[0].text
def test_reject_invalid():
    for data in [b'',b'garbage',b'x'* (5*1024*1024+1)]:
        with pytest.raises(ValueError):parse_docx(data)
def test_rules():
    with pytest.raises(ValueError):validate_rules([])
    with pytest.raises(ValueError):validate_rules(['short'])
def test_verified_quote():
    b=parse_docx(make_doc());r=validate_rules(['Flag numerical performance disclosures'])
    good={'block_id':'p1','rule_id':'R1','quote':'50 km','explanation':'Numeric range'}
    bad={**good,'quote':'100 km'}
    a,n=validate_findings([good,bad,good],b,r)
    assert len(a)==1 and n==1
def test_no_global_api_key_fallback(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','sk-should-not-be-used-ever-123')
    with pytest.raises(ValueError,match='API key'):
        analyze(parse_docx(make_doc()),validate_rules(['Flag numeric performance specifications']))
