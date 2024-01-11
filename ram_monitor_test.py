from fastapi.testclient import TestClient
from ram_monitor_api import app

client = TestClient(app)

def test_record_ram():
    response = client.post("/record-ram-usage")
    assert response.status_code == 200
    assert response.json() == {"message": "RAM usage recorded successfully"}

def test_get_last_records():
    # Record RAM usage a few times to have data for testing
    for _ in range(5):
        client.post("/record-ram-usage")

    response = client.get("/get-last-records?n=3")
    assert response.status_code == 200
    records = response.json()
    assert len(records) == 3

if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
