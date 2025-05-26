from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.models import AIPrompt # Ensure this path is correct

# Test data
PROMPT_DATA_VALID = {
    "name": "test_prompt_unique",
    "description": "A unique test prompt.",
    "prompt_text": "This is the text for the unique test prompt."
}
PROMPT_DATA_VALID_2 = {
    "name": "test_prompt_another",
    "description": "Another test prompt.",
    "prompt_text": "Text for another prompt."
}
PROMPT_DATA_DUPLICATE_NAME = { # Will use PROMPT_DATA_VALID's name
    "name": "test_prompt_unique", 
    "description": "A different description for a duplicate name.",
    "prompt_text": "Different text."
}

# --- POST /admin/config/prompts ---
def test_create_ai_prompt_success_admin(client: TestClient, admin_auth_headers: dict, db_session: Session):
    response = client.post("/admin/config/prompts/", headers=admin_auth_headers, json=PROMPT_DATA_VALID)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == PROMPT_DATA_VALID["name"]
    assert data["description"] == PROMPT_DATA_VALID["description"]
    assert "id" in data
    
    # Verify in DB
    db_prompt = db_session.query(AIPrompt).filter(AIPrompt.id == data["id"]).first()
    assert db_prompt is not None
    assert db_prompt.name == PROMPT_DATA_VALID["name"]

def test_create_ai_prompt_duplicate_name_admin(client: TestClient, admin_auth_headers: dict, db_session: Session):
    # First, create an initial prompt
    client.post("/admin/config/prompts/", headers=admin_auth_headers, json=PROMPT_DATA_VALID)
    
    # Attempt to create another with the same name
    response_duplicate = client.post("/admin/config/prompts/", headers=admin_auth_headers, json=PROMPT_DATA_DUPLICATE_NAME)
    assert response_duplicate.status_code == 400 # Expect Bad Request for duplicate
    assert "já existe" in response_duplicate.json()["detail"]

def test_create_ai_prompt_unauthorized_editor(client: TestClient, editor_auth_headers: dict):
    response = client.post("/admin/config/prompts/", headers=editor_auth_headers, json=PROMPT_DATA_VALID)
    assert response.status_code == 403 # Expect Forbidden

# --- GET /admin/config/prompts ---
def test_list_ai_prompts_success_admin(client: TestClient, admin_auth_headers: dict, seed_initial_prompts):
    # seed_initial_prompts fixture ensures there's data
    response = client.get("/admin/config/prompts/", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 5 # Based on seeded data
    # Check if one of the seeded prompts is present
    assert any(p["name"] == "rfp_analysis_system_role" for p in data)

def test_list_ai_prompts_unauthorized_editor(client: TestClient, editor_auth_headers: dict):
    response = client.get("/admin/config/prompts/", headers=editor_auth_headers)
    assert response.status_code == 403

# --- GET /admin/config/prompts/{prompt_id} ---
def test_get_ai_prompt_by_id_success_admin(client: TestClient, admin_auth_headers: dict, db_session: Session):
    # Create a prompt to fetch
    create_response = client.post("/admin/config/prompts/", headers=admin_auth_headers, json=PROMPT_DATA_VALID)
    prompt_id = create_response.json()["id"]

    response = client.get(f"/admin/config/prompts/{prompt_id}", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == prompt_id
    assert data["name"] == PROMPT_DATA_VALID["name"]

def test_get_ai_prompt_by_id_not_found_admin(client: TestClient, admin_auth_headers: dict):
    non_existent_id = 99999
    response = client.get(f"/admin/config/prompts/{non_existent_id}", headers=admin_auth_headers)
    assert response.status_code == 404

def test_get_ai_prompt_by_id_unauthorized_editor(client: TestClient, editor_auth_headers: dict, db_session: Session, admin_auth_headers: dict):
    # Create a prompt first as admin
    create_response = client.post("/admin/config/prompts/", headers=admin_auth_headers, json=PROMPT_DATA_VALID)
    prompt_id = create_response.json()["id"]
    
    response = client.get(f"/admin/config/prompts/{prompt_id}", headers=editor_auth_headers)
    assert response.status_code == 403

# --- GET /admin/config/prompts/by_name/{prompt_name} ---
def test_get_ai_prompt_by_name_success_any_user(client: TestClient, admin_auth_headers: dict, seed_initial_prompts, editor_auth_headers: dict):
    prompt_name_to_fetch = "rfp_analysis_system_role" # From seeded data
    
    # Test with admin
    response_admin = client.get(f"/admin/config/prompts/by_name/{prompt_name_to_fetch}", headers=admin_auth_headers)
    assert response_admin.status_code == 200
    data_admin = response_admin.json()
    assert data_admin["name"] == prompt_name_to_fetch

    # Test with editor (should also succeed as this endpoint has no admin_only check)
    response_editor = client.get(f"/admin/config/prompts/by_name/{prompt_name_to_fetch}", headers=editor_auth_headers)
    assert response_editor.status_code == 200
    data_editor = response_editor.json()
    assert data_editor["name"] == prompt_name_to_fetch
    
    # Test without any auth (should also succeed)
    response_no_auth = client.get(f"/admin/config/prompts/by_name/{prompt_name_to_fetch}")
    assert response_no_auth.status_code == 200
    data_no_auth = response_no_auth.json()
    assert data_no_auth["name"] == prompt_name_to_fetch


def test_get_ai_prompt_by_name_not_found(client: TestClient):
    non_existent_name = "this_prompt_does_not_exist_ever"
    response = client.get(f"/admin/config/prompts/by_name/{non_existent_name}") # No auth needed
    assert response.status_code == 404

# --- PUT /admin/config/prompts/{prompt_id} ---
def test_update_ai_prompt_success_admin(client: TestClient, admin_auth_headers: dict, db_session: Session):
    # Create a prompt
    create_response = client.post("/admin/config/prompts/", headers=admin_auth_headers, json=PROMPT_DATA_VALID)
    prompt_id = create_response.json()["id"]
    
    update_data = {"name": "updated_prompt_name", "description": "Updated description."}
    response = client.put(f"/admin/config/prompts/{prompt_id}", headers=admin_auth_headers, json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["prompt_text"] == PROMPT_DATA_VALID["prompt_text"] # Text should remain if not updated

    # Verify in DB
    db_prompt = db_session.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()
    assert db_prompt.name == update_data["name"]

def test_update_ai_prompt_duplicate_name_conflict_admin(client: TestClient, admin_auth_headers: dict, db_session: Session):
    # Create prompt1
    client.post("/admin/config/prompts/", headers=admin_auth_headers, json=PROMPT_DATA_VALID) # name: "test_prompt_unique"
    # Create prompt2
    create_response_2 = client.post("/admin/config/prompts/", headers=admin_auth_headers, json=PROMPT_DATA_VALID_2) # name: "test_prompt_another"
    prompt2_id = create_response_2.json()["id"]

    # Try to update prompt2's name to prompt1's name
    update_data_conflict = {"name": PROMPT_DATA_VALID["name"]} 
    response = client.put(f"/admin/config/prompts/{prompt2_id}", headers=admin_auth_headers, json=update_data_conflict)
    assert response.status_code == 400
    assert "já existe" in response.json()["detail"]


def test_update_ai_prompt_not_found_admin(client: TestClient, admin_auth_headers: dict):
    non_existent_id = 99999
    update_data = {"name": "some_name"}
    response = client.put(f"/admin/config/prompts/{non_existent_id}", headers=admin_auth_headers, json=update_data)
    assert response.status_code == 404

def test_update_ai_prompt_unauthorized_editor(client: TestClient, editor_auth_headers: dict, admin_auth_headers: dict, db_session: Session):
    create_response = client.post("/admin/config/prompts/", headers=admin_auth_headers, json=PROMPT_DATA_VALID)
    prompt_id = create_response.json()["id"]
    
    update_data = {"name": "updated_by_editor_attempt"}
    response = client.put(f"/admin/config/prompts/{prompt_id}", headers=editor_auth_headers, json=update_data)
    assert response.status_code == 403

# --- DELETE /admin/config/prompts/{prompt_id} ---
def test_delete_ai_prompt_success_admin(client: TestClient, admin_auth_headers: dict, db_session: Session):
    create_response = client.post("/admin/config/prompts/", headers=admin_auth_headers, json=PROMPT_DATA_VALID)
    prompt_id = create_response.json()["id"]

    response = client.delete(f"/admin/config/prompts/{prompt_id}", headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.json()["ok"] is True
    
    # Verify in DB
    db_prompt = db_session.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()
    assert db_prompt is None

def test_delete_ai_prompt_not_found_admin(client: TestClient, admin_auth_headers: dict):
    non_existent_id = 99999
    response = client.delete(f"/admin/config/prompts/{non_existent_id}", headers=admin_auth_headers)
    assert response.status_code == 404

def test_delete_ai_prompt_unauthorized_editor(client: TestClient, editor_auth_headers: dict, admin_auth_headers: dict, db_session: Session):
    create_response = client.post("/admin/config/prompts/", headers=admin_auth_headers, json=PROMPT_DATA_VALID)
    prompt_id = create_response.json()["id"]
    
    response = client.delete(f"/admin/config/prompts/{prompt_id}", headers=editor_auth_headers)
    assert response.status_code == 403
    
    # Verify it was not deleted
    db_prompt = db_session.query(AIPrompt).filter(AIPrompt.id == prompt_id).first()
    assert db_prompt is not None
