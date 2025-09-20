import pytest
import os
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Load test environment variables
load_dotenv('.env.test')
# Prefer isolated in-memory DB for tests to avoid FK teardown issues
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

# Import app and database
from main import app
from database import Base, get_db
try:
    from services.llm_service import llm_service  # type: ignore
except Exception:
    from llm_service import llm_service  # fallback for flat layout

try:
    from services.rag_service import rag_service  # type: ignore
except Exception:
    from rag_service import rag_service  # fallback for flat layout
from services.trello_service import TrelloService
from services.simple_pdf_service import SimplePDFService
from services.pricing_resolver import pricing_resolver
from services.estimation_service import estimation_service

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration"""
    return {
        "database_url": os.getenv("DATABASE_URL"),
        "testing": os.getenv("TESTING", "True") == "True",
        "langfuse_secret_key": os.getenv("LANGFUSE_SECRET_KEY"),
        "langfuse_public_key": os.getenv("LANGFUSE_PUBLIC_KEY"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "trello_api_key": os.getenv("TRELLO_API_KEY"),
        "trello_api_token": os.getenv("TRELLO_API_TOKEN"),
    }

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    database_url = os.getenv("DATABASE_URL")
    
    if "sqlite" in database_url:
        # Use SQLite for testing if specified
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
    else:
        # Use PostgreSQL for testing
        engine = create_engine(database_url)
    
    return engine

@pytest.fixture(scope="session")
def setup_test_database(test_engine):
    """Set up test database schema"""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Drop all tables after tests
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def test_db_session(test_engine, setup_test_database):
    """Create a test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        app.dependency_overrides.clear()

@pytest.fixture
def test_client(test_db_session):
    """Create test client with database session"""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def mock_langfuse():
    """Mock Langfuse client"""
    from tests.utils import create_mock_langfuse
    return create_mock_langfuse()

@pytest.fixture
def mock_openai():
    """Mock OpenAI client"""
    from tests.utils import create_mock_openai
    return create_mock_openai()

@pytest.fixture
def mock_llm_service(mock_openai):
    """Mock LLM service with OpenAI client"""
    with patch.object(llm_service, 'openai_client', mock_openai):
        with patch.object(llm_service, 'is_configured', return_value=True):
            yield llm_service

@pytest.fixture
def mock_rag_service():
    """Mock RAG service"""
    # Patch ChromaDB to use in-memory for testing
    with patch('services.rag_service.chromadb.Client') as mock_client:
        mock_collection = Mock()
        mock_collection.get.return_value = {'ids': []}
        mock_collection.query.return_value = {
            'ids': [['1']],
            'documents': [['Test document content']],
            'metadatas': [[{'title': 'Test Document', 'source': 'test', 'type': 'test'}]],
            'distances': [[0.1]]
        }
        
        mock_client.return_value.get_collection.return_value = mock_collection
        mock_client.return_value.create_collection.return_value = mock_collection
        
        yield rag_service

@pytest.fixture
def mock_trello_service():
    """Mock Trello service"""
    service = TrelloService()
    
    # Mock Trello API calls
    with patch.object(service, '_make_trello_request') as mock_request:
        mock_request.return_value = {
            'id': 'board_123',
            'name': 'Test Board',
            'lists': [
                {'id': 'list_1', 'name': 'To Do'},
                {'id': 'list_2', 'name': 'In Progress'}
            ]
        }
        
        yield service

@pytest.fixture
def pdf_service():
    """PDF service fixture"""
    service = SimplePDFService()
    # Use test output directory
    service.output_dir = os.path.join(os.path.dirname(__file__), 'test_data', 'pdf_output')
    os.makedirs(service.output_dir, exist_ok=True)
    return service

@pytest.fixture
def pricing_service():
    """Pricing service fixture"""
    return pricing_resolver

@pytest.fixture
def estimation_service_fixture():
    """Estimation service fixture"""
    return estimation_service

@pytest.fixture(autouse=True)
def auto_cleanup():
    """Automatic cleanup after tests"""
    # Setup
    yield
    # Teardown - clear any test files
    test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    if os.path.exists(test_data_dir):
        for file in os.listdir(test_data_dir):
            if file.endswith('.pdf') or file.endswith('.tmp'):
                os.remove(os.path.join(test_data_dir, file))
