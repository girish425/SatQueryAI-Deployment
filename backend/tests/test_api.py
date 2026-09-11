import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_api_upload_geotiff():
    sample_path = "./sample_data/sample_optical_hyderabad.tif"
    with open(sample_path, "rb") as f:
        response = client.post(
            "/upload/",
            files={"file": ("test_optical.tif", f, "image/tiff")}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "file_id" in data
    assert "preview_url" in data
    assert data["bands"] == 3


def test_api_chat_flow():
    # Chat with sample optical image
    response = client.post(
        "/chat/",
        json={
            "query": "What is visible in this image?",
            "image_ids": ["sample_optical_hyderabad.tif"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["intent"] == "image_understanding"
    assert "summary" in data["answer"]
    assert "key_findings" in data["answer"]
    assert len(data["answer"]["key_findings"]) > 0
    session_id = data["session_id"]

    # Retrieve history
    hist_resp = client.get(f"/history/{session_id}")
    assert hist_resp.status_code == 200
    assert len(hist_resp.json()["conversation"]["messages"]) >= 2

    # Download PDF
    pdf_resp = client.get(f"/conversation/{session_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert len(pdf_resp.content) > 1000


def test_bigearthnet_catalog():
    response = client.get("/retrieve/bigearthnet")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "citation" in data
    assert data["citation"]["arxiv_id"] == "2603.29630"
    assert data["count"] >= 3
    first_patch = data["results"][0]
    assert "sentinel2_file" in first_patch
    assert "sentinel1_file" in first_patch
    assert "caption" in first_patch
    assert "vqa_pairs" in first_patch


def test_bigearthnet_select_pair():
    response = client.post("/retrieve/select-bigearthnet/BEN-MM-AUT-VALLEY-01?mode=pair")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["staged_items"]) == 2  # S1 and S2
    assert "caption" in data
    assert len(data["vqa_pairs"]) > 0


def test_live_stac_search_mumbai():
    """Verify live STAC query geocodes Mumbai and queries Earth Search STAC API"""
    response = client.get("/retrieve/results?query=Mumbai&satellite=Sentinel-2&cloud_cover=40")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["success", "empty"]
    assert "Earth Search" in data["source"]
    assert data["sensor"] == "Sentinel-2 MSI"
    if data["status"] == "success":
        assert len(data["results"]) > 0
        first = data["results"][0]
        assert "Mumbai" in first["location"]
        assert "thumbnail_url" in first


def test_live_stac_empty_state_no_fallback():
    """Verify non-existent location returns status 'empty' with 0 results and NO hardcoded fallbacks"""
    response = client.get("/retrieve/results?query=unknownnonexistentregion9999")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "empty"
    assert data["count"] == 0
    assert len(data["results"]) == 0
    assert "Could not determine geographical coordinates" in data["message"]


def test_live_stac_select_image():
    """Verify staging a real-time STAC acquisition into chat session"""
    response = client.post(
        "/retrieve/select-stac",
        params={
            "item_id": "S2A_TEST_MUMBAI_SCENE",
            "preview_url": "",
            "title": "Sentinel-2 MSI Mumbai Coastline",
            "platform": "Sentinel-2"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "stac_" in data["filename"]
    assert data["preview_url"].startswith("/evidence/")
    assert "512" in str(data["dimensions"])


def test_database_health_endpoint():
    """Verify dedicated database health-check endpoint reports status, database name, and masked URI"""
    response = client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["connected", "disconnected"]
    assert data["database"] == "satquery_ai"
    assert "uri" in data
    assert "****" in data["uri"] or "Not Configured" in data["uri"]
    assert "fallback_active" in data


def test_database_never_exposes_password():
    """Verify password is never exposed in any health or history responses"""
    for endpoint in ["/health", "/health/db", "/history/db/status"]:
        res = client.get(endpoint)
        assert res.status_code == 200
        text = res.text
        # Ensure raw password string from .env is not present in response
        assert "Anu.2486" not in text
        assert "<Anu.2486>" not in text


def test_history_save_and_retrieve():
    """Verify storing and retrieving conversation history with all metadata fields"""
    test_session = "test-session-mongo-verify-123"
    save_resp = client.post(
        "/history/save",
        json={
            "session_id": test_session,
            "title": "Test Coastal Assessment",
            "selected_model": "RS-Image-Understanding-Baseline",
            "image_references": ["sample_optical_hyderabad.tif"],
            "messages": [
                {
                    "session_id": test_session,
                    "role": "user",
                    "query": "Assess water bodies",
                    "image_references": ["sample_optical_hyderabad.tif"],
                    "timestamp": "2026-09-11T20:00:00Z"
                },
                {
                    "session_id": test_session,
                    "role": "assistant",
                    "query": "Assess water bodies",
                    "ai_response": {"summary": "Water body confirmed in scene"},
                    "selected_model": "RS-Image-Understanding-Baseline",
                    "image_references": ["sample_optical_hyderabad.tif"],
                    "timestamp": "2026-09-11T20:00:05Z"
                }
            ]
        }
    )
    assert save_resp.status_code == 200
    assert save_resp.json()["status"] == "success"

    # Retrieve and verify
    get_resp = client.get(f"/history/{test_session}")
    assert get_resp.status_code == 200
    conv = get_resp.json()["conversation"]
    assert conv["session_id"] == test_session
    assert conv["title"] == "Test Coastal Assessment"
    assert len(conv["messages"]) == 2
    assert conv["messages"][0]["query"] == "Assess water bodies"
    assert "ai_response" in conv["messages"][1]

    # Clean up
    del_resp = client.delete(f"/history/{test_session}")
    assert del_resp.status_code == 200

