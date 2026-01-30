"""
Test suite for FastWebDrop backend operations.
Covers critical functionality: add, delete, update, export, import.

Run with: pytest tests/test_fast_api_main.py -v
"""

import pytest
import json
import os
import sys
import tempfile
from fastapi.testclient import TestClient
from io import BytesIO

# Add parent directory to path to import fast_api_main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fast_api_main import app, load_links, save_links, LINKS_FILE, verify_auth


# Mock authentication to bypass auth in tests
async def mock_verify_auth():
    return "test_user"


# Override the auth dependency
app.dependency_overrides[verify_auth] = mock_verify_auth


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def temp_links_file(monkeypatch):
    """Create a temporary links file for isolated testing."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    temp_file.write('[]')
    temp_file.close()

    # Patch the LINKS_FILE constant
    monkeypatch.setattr('fast_api_main.LINKS_FILE', temp_file.name)

    yield temp_file.name

    # Cleanup
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)


# Test 1: Add a new link
def test_add_link_success(client, temp_links_file):
    """Test adding a new link successfully."""
    response = client.post("/add-link", json={"url": "https://example.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # Verify link was saved
    links = load_links()
    assert len(links) == 1
    assert links[0]["url"] == "https://example.com"
    assert links[0]["category"] == "working"
    assert "timestamp" in links[0]
    assert "ip" in links[0]


# Test 2: Prevent duplicate links
def test_add_duplicate_link(client, temp_links_file):
    """Test that duplicate links are rejected."""
    # Add first link
    client.post("/add-link", json={"url": "https://duplicate.com"})

    # Try to add same link again
    response = client.post("/add-link", json={"url": "https://duplicate.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "duplicate"

    # Verify only one link exists
    links = load_links()
    assert len(links) == 1


# Test 3: Delete a link
def test_delete_link(client, temp_links_file):
    """Test deleting an existing link."""
    # Add a link first
    client.post("/add-link", json={"url": "https://todelete.com"})
    assert len(load_links()) == 1

    # Delete it
    response = client.post("/delete-link", json={"url": "https://todelete.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # Verify link was deleted
    links = load_links()
    assert len(links) == 0


# Test 4: Update link category
def test_update_category(client, temp_links_file):
    """Test updating a link's category."""
    # Add a link
    client.post("/add-link", json={"url": "https://categorize.com"})

    # Update category
    response = client.post("/update-category", json={
        "url": "https://categorize.com",
        "category": "archived"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # Verify category was updated
    links = load_links()
    assert links[0]["category"] == "archived"


# Test 5: Export links as JSON
def test_export_json(client, temp_links_file):
    """Test exporting links to JSON format."""
    # Add test data
    client.post("/add-link", json={"url": "https://export1.com"})
    client.post("/add-link", json={"url": "https://export2.com"})

    # Export
    response = client.get("/export-json")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "attachment" in response.headers["content-disposition"]

    # Verify exported data
    exported = json.loads(response.text)
    assert len(exported) == 2
    assert exported[0]["url"] == "https://export1.com"


# Test 6: Export links as CSV
def test_export_csv(client, temp_links_file):
    """Test exporting links to CSV format."""
    # Add test data
    client.post("/add-link", json={"url": "https://csvtest.com"})

    # Export
    response = client.get("/export-csv")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]

    # Verify CSV header
    csv_content = response.text
    assert "url,timestamp,ip,category" in csv_content
    assert "https://csvtest.com" in csv_content


# Test 7: Import links from JSON
def test_import_json(client, temp_links_file):
    """Test importing links from a JSON file."""
    import_data = [
        {"url": "https://import1.com", "category": "working", "timestamp": "2024-01-01T00:00:00", "ip": "127.0.0.1"},
        {"url": "https://import2.com", "category": "archived", "timestamp": "2024-01-02T00:00:00", "ip": "127.0.0.1"}
    ]

    # Create file-like object
    file_content = json.dumps(import_data).encode()
    files = {"file": ("links.json", BytesIO(file_content), "application/json")}

    # Import
    response = client.post("/import-links", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["added"] == 2

    # Verify imported links
    links = load_links()
    assert len(links) == 2


# Test 8: Import links from CSV
def test_import_csv(client, temp_links_file):
    """Test importing links from a CSV file."""
    csv_data = """url,timestamp,ip,category
https://csvimport1.com,2024-01-01T00:00:00,127.0.0.1,working
https://csvimport2.com,2024-01-02T00:00:00,127.0.0.1,archived"""

    # Create file-like object
    files = {"file": ("links.csv", BytesIO(csv_data.encode()), "text/csv")}

    # Import
    response = client.post("/import-links", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["added"] == 2

    # Verify imported links
    links = load_links()
    assert len(links) == 2
    assert links[0]["url"] == "https://csvimport1.com"


# Test 9: Load links from file
def test_load_links(temp_links_file):
    """Test loading links from storage file."""
    # Write test data directly
    test_links = [{"url": "https://test.com", "category": "working", "timestamp": "2024-01-01T00:00:00", "ip": "127.0.0.1"}]
    with open(temp_links_file, 'w') as f:
        json.dump(test_links, f)

    # Load links
    links = load_links()
    assert len(links) == 1
    assert links[0]["url"] == "https://test.com"


# Test 10: Save links to file
def test_save_links(temp_links_file):
    """Test saving links to storage file."""
    test_links = [
        {"url": "https://save1.com", "category": "working", "timestamp": "2024-01-01T00:00:00", "ip": "127.0.0.1"},
        {"url": "https://save2.com", "category": "archived", "timestamp": "2024-01-02T00:00:00", "ip": "127.0.0.1"}
    ]

    # Save links
    save_links(test_links)

    # Verify saved data
    with open(temp_links_file, 'r') as f:
        saved = json.load(f)

    assert len(saved) == 2
    assert saved[0]["url"] == "https://save1.com"
    assert saved[1]["url"] == "https://save2.com"
