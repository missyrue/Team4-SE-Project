"""Smoke test: proves the project builds and the CI pipeline runs (first green tick)."""


def test_app_starts_and_health_endpoint_answers(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_page_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Online Bookstore" in response.text
