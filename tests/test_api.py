from fastapi.testclient import TestClient
from app.main import app


def test_health():
    r=TestClient(app).get('/health')
    assert r.status_code==200 and r.json()['status']=='ok'


def test_inference_demo():
    r=TestClient(app).post('/v1/inference',json={'tenant_id':'api-test','prompt':'hello'})
    assert r.status_code==200
    assert r.json()['text']=='Synthetic successful response'
