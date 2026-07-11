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

# Force mock mode on Notion MCP client to prevent hitting the real workspace in tests
@pytest.fixture(autouse=True)
def mock_notion_sync():
    """Mocks out NotionMCPClient direct API calls to prevent real network requests in unit tests."""
    with patch('mcp.notion_mcp_client.NotionMCPClient._execute_direct_api') as mock_api:
        mock_api.return_value = {
            "id": "mock_page_id_xyz",
            "url": "https://notion.so/mock_page_id_xyz"
        }
        yield mock_api

@pytest.fixture(name="session")
def session_fixture() -> Generator[Session, None, None]:
    """Creates a temporary in-memory SQLite database session for unit tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session

