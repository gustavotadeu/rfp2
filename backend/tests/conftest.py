import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os
from typing import Generator, Any

# Set environment variable for test database before other imports
os.environ['TESTING'] = 'True' 
# This ensures that if your main app or models.py tries to connect to DB at import time, it might use this
# However, the explicit engine override is more reliable.

from backend.main import app # Ensure this is your FastAPI app instance
from backend.models import Base, User # Your SQLAlchemy Base and User model
from backend.database import SessionLocal, engine as main_engine # Original engine
from backend.auth import get_db, get_password_hash, create_access_token

# --- Test Database Setup ---
SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL_TEST,
    connect_args={"check_same_thread": False}, # Needed for SQLite
    poolclass=StaticPool, # Use StaticPool for SQLite in-memory
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Override get_db dependency for tests
def override_get_db() -> Generator[Session, Any, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Create all tables in the in-memory SQLite database
    # This will apply all model definitions including AIPrompt
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(setup_test_database) -> Generator[Session, Any, None]:
    """Provides a clean database session for each test function."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback() # Ensure no changes persist if a test fails mid-transaction
        db.close()

@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, Any, None]: # client depends on db_session to ensure DB is ready
    """Provides a TestClient instance for making API requests."""
    # db_session fixture ensures tables are created and session is managed
    yield TestClient(app)


# --- Test User and Auth Fixtures ---
@pytest.fixture(scope="function")
def test_admin_user(db_session: Session) -> User:
    admin_user = User(
        nome="Admin User",
        email="admin@example.com",
        senha_hash=get_password_hash("adminpass"),
        perfil="admin",
        ativo=True
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)
    return admin_user

@pytest.fixture(scope="function")
def test_editor_user(db_session: Session) -> User:
    editor_user = User(
        nome="Editor User",
        email="editor@example.com",
        senha_hash=get_password_hash("editorpass"),
        perfil="editor", # Non-admin profile
        ativo=True
    )
    db_session.add(editor_user)
    db_session.commit()
    db_session.refresh(editor_user)
    return editor_user

@pytest.fixture(scope="function")
def admin_auth_headers(test_admin_user: User) -> dict:
    access_token = create_access_token(data={"sub": test_admin_user.email})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def editor_auth_headers(test_editor_user: User) -> dict:
    access_token = create_access_token(data={"sub": test_editor_user.email})
    return {"Authorization": f"Bearer {access_token}"}

# Fixture to pre-seed prompts for tests that need them
@pytest.fixture(scope="function")
def seed_initial_prompts(db_session: Session):
    from backend.models import AIPrompt # Import here to avoid circular dependency issues at top level
    import datetime

    prompts_data = [
        {
            'name': "rfp_analysis_system_role",
            'description': "System role for RFP analysis AI.",
            'prompt_text': "You are an AI assistant for RFP analysis.",
            'created_at': datetime.datetime.utcnow(),
            'updated_at': datetime.datetime.utcnow()
        },
        {
            'name': "rfp_analysis_user_prompt",
            'description': "User prompt for RFP analysis.",
            'prompt_text': "Analyze this RFP: {text}",
            'created_at': datetime.datetime.utcnow(),
            'updated_at': datetime.datetime.utcnow()
        },
         {
            'name': "vendor_matching_system_role",
            'description': "System role for vendor matching.",
            'prompt_text': "You are an AI for matching vendors.",
            'created_at': datetime.datetime.utcnow(),
            'updated_at': datetime.datetime.utcnow()
        },
        {
            'name': "vendor_matching_user_prompt",
            'description': "User prompt for vendor matching.",
            'prompt_text': "Match vendors for: {rfp_summary} with {vendors_info}",
            'created_at': datetime.datetime.utcnow(),
            'updated_at': datetime.datetime.utcnow()
        },
        {
            'name': "technical_proposal_user_prompt",
            'description': "User prompt for technical proposal generation.",
            'prompt_text': "Generate proposal for {rfp_nome} etc.",
            'created_at': datetime.datetime.utcnow(),
            'updated_at': datetime.datetime.utcnow()
        }
    ]
    for prompt_dict in prompts_data:
        db_prompt = AIPrompt(**prompt_dict)
        db_session.add(db_prompt)
    db_session.commit()
    return prompts_data # Return the data for potential use in tests
