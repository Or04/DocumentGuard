"""Delivery regression tests against the local FastAPI application."""
import io, json
from docx import Document
from fastapi.testclient import TestClient
from app.main import app
from app.core import Block,validate_findings,validate_rules,parse_docx

client=TestClient(app)

def make_doc(paragraphs=(),tables=()):
    doc=Document()
    for text in paragraphs:doc.add_paragraph(text)
    for cells in tables:
        t=doc.add_table(rows=1,cols=len(cells))
        for cell,text in zip(t.rows[0].cells,cells):cell.text=text
    output=io.BytesIO();doc.save(output);return output.getvalue()

def request(blob,rules, key='sk-fake-for-testing-never-real-1234'):
    data={'rules':json.dumps(rules)}
    return client.post('/api/analyze',files={'file':('example.docx',blob,'application/vnd.openxmlformats-officedocument.wordprocessingml.document')},data=data,headers={'Authorization':'Bearer '+key} if key is not None else {})

def test_full_sample_document_parses():
    from pathlib import Path
    p=Path('/mnt/data/documentguard_sample_test.docx')
    if p.exists():
        blocks=parse_docx(p.read_bytes())
        assert len(blocks)>5
        assert any(b.text for b in blocks if b.id.startswith('t'))

def test_without_key_fails_closed():
    blob=make_doc(['The detection range is 50 km.'])
    assert request(blob,['Flag numeric operational performance'],key=None).status_code==400

def test_tables_are_parsed():
    blocks=parse_docx(make_doc(tables=[['Detection range is 50 km','Public']]))
    assert any('Table 1' in b.location for b in blocks)

def test_rule_restrictions():
    blob=make_doc(['Detection range is 50 km'])
    assert request(blob,['short']).status_code==400
    assert request(blob,['valid rule']*16).status_code==400

def test_oversized_upload():
    assert request(b'x'*(5*1024*1024+1),['Flag numeric performance']).status_code==400

def test_evidence_hallucination_rejected():
    blocks=[Block('p1','Paragraph 1','Detection range is 50 km.')]
    rules=validate_rules(['Flag numeric detection range'])
    findings=[{'rule_id':'R1','block_id':'p1','quote':'Detection range is 500 km.','explanation':'invented'}, {'rule_id':'R1','block_id':'p1','quote':'Detection range is 50 km.','explanation':'exact'}]
    accepted,rejected=validate_findings(findings,blocks,rules)
    assert rejected==1 and len(accepted)==1

def test_duplicate_evidence_removed():
    blocks=[Block('p1','Paragraph 1','Detection range is 50 km.')]
    rules=validate_rules(['Flag numeric detection range'])
    f={'rule_id':'R1','block_id':'p1','quote':'Detection range is 50 km.'}
    accepted,rejected=validate_findings([f,f],blocks,rules)
    assert len(accepted)==1 and rejected==0

class FakeResponse:
    def __init__(self,payload):
        self.choices=[type('Choice',(),{'message':type('Msg',(),{'content':json.dumps(payload)})()})()]
class FakeClient:
    def __init__(self,responses):
        self.responses=iter(responses)
        self.chat=type('Chat',(),{})()
        self.chat.completions=type('Completions',(),{'create':lambda _,**kwargs:FakeResponse(next(self.responses))})()

def test_full_semantic_flow_with_mocked_model():
    from app.core import analyze
    blocks=parse_docx(make_doc(['The detection range is 50 km.']))
    rules=validate_rules(['Flag numeric detection range disclosures'])
    proposal={'findings':[{'rule_id':'R1','block_id':'p1','quote':'detection range is 50 km','explanation':'Performance disclosure'}]}
    result=analyze(blocks,rules,client=FakeClient([proposal,{'decision':'confirmed','reason':'Clear numeric range'}]))
    assert result['count']==1
    assert result['violations'][0]['status']=='evidence_verified'

def test_hallucinated_evidence_never_reaches_semantic_review():
    from app.core import analyze
    blocks=parse_docx(make_doc(['The detection range is 50 km.']))
    rules=validate_rules(['Flag numeric detection range disclosures'])
    proposal={'findings':[{'rule_id':'R1','block_id':'p1','quote':'detection range is 500 km','explanation':'Fabricated'}]}
    result=analyze(blocks,rules,client=FakeClient([proposal]))
    assert result['count']==0 and result['rejected_unverified']==1

def test_ambiguous_evidence_requires_human_review():
    from app.core import analyze
    blocks=parse_docx(make_doc(['The system does not have a detection range of 50 km.']))
    rules=validate_rules(['Flag disclosures of detection range'])
    proposal={'findings':[{'rule_id':'R1','block_id':'p1','quote':'detection range of 50 km','explanation':'Potential'}]}
    result=analyze(blocks,rules,client=FakeClient([proposal,{'decision':'uncertain','reason':'Negated claim'}]))
    assert result['violations'][0]['status']=='needs_human_review'

def test_semantic_rejection():
    from app.core import analyze
    blocks=parse_docx(make_doc(['The system does not have a detection range of 50 km.']))
    rules=validate_rules(['Flag confirmed detection ranges'])
    proposal={'findings':[{'rule_id':'R1','block_id':'p1','quote':'detection range of 50 km','explanation':'Potential'}]}
    result=analyze(blocks,rules,client=FakeClient([proposal,{'decision':'rejected','reason':'Negation'}]))
    assert result['count']==0 and result['rejected_unverified']==1
