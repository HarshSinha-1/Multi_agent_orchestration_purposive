import os
import json
from typing import Any, Optional, Type
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
from shared.utils.logging import get_logger

load_dotenv()

logger = get_logger(__name__)

class GroqClient:
    """Wraps Groq API client to execute chat completions and structured outputs."""
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in environment. Running in SIMULATED (mock) mode.")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)

    def chat_completion(self, messages: list[dict], system_prompt: Optional[str] = None) -> str:
        """Sends a standard chat completion request to Groq."""
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        if not self.client:
            logger.info("[MOCK COMPLETION] Simulating response for messages: %s", messages)
            return "This is a simulated response because GROQ_API_KEY is not set. Please set the API key in the .env file."

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            raise e

    def structured_chat(self, messages: list[dict], system_prompt: Optional[str] = None, response_schema: Type[BaseModel] = None) -> Any:
        """
        Requests a structured response matching the Pydantic schema using JSON mode.
        """
        if not response_schema:
            raise ValueError("response_schema is required for structured output.")

        schema_json = json.dumps(response_schema.model_json_schema())
        instruction = f"\n\nYou MUST respond with valid JSON that matches the following JSON Schema:\n{schema_json}"
        
        # Inject instruction to the system prompt or last message to guide JSON output format
        if system_prompt:
            system_prompt_updated = system_prompt + instruction
        else:
            system_prompt_updated = "You are a helpful assistant." + instruction

        if not self.client:
            logger.info("[MOCK STRUCTURED CHAT] Simulating schema output for: %s", response_schema.__name__)
            # Return dummy object of the schema
            return self._generate_mock_schema_data(response_schema)

        try:
            # We enforce json response format
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "system", "content": system_prompt_updated}] + messages,
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            content = response.choices[0].message.content or "{}"
            parsed_data = json.loads(content)
            return response_schema.model_validate(parsed_data)
        except Exception as e:
            logger.error(f"Error calling structured Groq API or parsing JSON: {e}")
            # Try a second time or raise
            raise e

    def _generate_mock_schema_data(self, schema: Type[BaseModel]) -> BaseModel:
        """Helper to create dummy data matching Pydantic schema in mock mode."""
        # Simple mock generator based on schema fields
        mock_fields = {}
        for name, field in schema.model_fields.items():
            field_type = field.annotation
            # Check basic types
            if field_type == str:
                mock_fields[name] = f"Mock {name}"
            elif field_type == float or field_type == int:
                mock_fields[name] = 1.0 if field_type == float else 1
            elif field_type == bool:
                mock_fields[name] = True
            elif getattr(field_type, '__origin__', None) == list:
                mock_fields[name] = []
            elif getattr(field_type, '__origin__', None) == dict:
                mock_fields[name] = {}
            elif isinstance(field_type, type) and issubclass(field_type, BaseModel):
                mock_fields[name] = self._generate_mock_schema_data(field_type)
            else:
                # Literal or fallback
                # check if Literal
                if hasattr(field_type, '__args__'):
                    mock_fields[name] = field_type.__args__[0]
                else:
                    mock_fields[name] = None
        
        try:
            return schema.model_validate(mock_fields)
        except Exception as e:
            logger.error(f"Failed to generate mock schema data for {schema.__name__}: {e}")
            # Absolute fallback: instantiate with empty dict if possible
            return schema.model_construct(**mock_fields)

# Global client instance
groq_client = GroqClient()
