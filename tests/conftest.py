import pytest
from typing import Generator
from sqlmodel import SQLModel, Session, create_engine
from unittest.mock import patch, MagicMock

# Force mock mode on Groq client during tests
@pytest.fixture(autouse=True)
def mock_groq():
    """Mocks out GroqClient to prevent network/credential requirements in tests."""
    with patch('orchestrator.groq_client.groq_client') as mock_client:
        # Define mock behaviors
        mock_client.chat_completion.return_value = "Mocked chat response content."
        
        # We return MagicMock instances for structured chat to bypass real schema parsing
        mock_client.structured_chat.side_effect = lambda messages, system_prompt, response_schema: MagicMock()
        yield mock_client

@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """Creates a temporary in-memory SQLite database session for unit tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session
