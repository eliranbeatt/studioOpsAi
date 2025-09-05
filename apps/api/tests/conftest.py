import pytest
import os
from dotenv import load_dotenv

# Load test environment variables
load_dotenv('.env.test')

@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration"""
    return {
        "database_url": os.getenv("DATABASE_URL"),
        "testing": os.getenv("TESTING", "True") == "True",
        "langfuse_secret_key": os.getenv("LANGFUSE_SECRET_KEY"),
        "langfuse_public_key": os.getenv("LANGFUSE_PUBLIC_KEY"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
    }

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Import and configure test database fixtures
# pytest_plugins = ['pytest_postgresql.factories']