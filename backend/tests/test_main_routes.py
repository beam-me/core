def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "Beam.me Orchestrator & Gateway"}

def test_get_history(client):
    response = client.get("/api/history")
    assert response.status_code == 200
    assert response.json() == []

def test_get_agents(client):
    response = client.get("/api/agents")
    assert response.status_code == 200
    agents = response.json()
    assert len(agents) > 0
    assert agents[0]["id"] == "hmao-orchestrator"
