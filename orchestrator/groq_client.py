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
        
        if not self.api_key or self.api_key == "your_groq_api_key_here":
            logger.warning("GROQ_API_KEY not found or is a placeholder in environment. Running in SIMULATED (mock) mode.")
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
            return self._generate_mock_schema_data(response_schema, messages)

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

    def _generate_mock_schema_data(self, schema: Type[BaseModel], messages: Optional[list[dict]] = None) -> BaseModel:
        """Helper to create dummy data matching Pydantic schema in mock mode."""
        logger.info(f"[_generate_mock_schema_data] schema name: {schema.__name__}, messages count: {len(messages) if messages else 0}")
        if schema.__name__ == "ResumeScreeningResult" and messages:
            # Dynamic mock generation based on resume keywords compared to JD requirements
            user_msg = ""
            for msg in messages:
                if msg.get("role") == "user":
                    user_msg = msg.get("content", "")
                    break
            
            import re
            jd_match = re.search(r"### Job Requirements:\s*(.*?)\s*### Resume Text:", user_msg, re.DOTALL)
            resume_match = re.search(r"### Resume Text:\s*(.*)", user_msg, re.DOTALL)
            
            jd_text = jd_match.group(1).lower() if jd_match else ""
            resume_text = resume_match.group(1).lower() if resume_match else ""
            logger.info(f"[ResumeScreeningResult MOCK] jd_text: {repr(jd_text)[:100]}, resume_text: {repr(resume_text)[:100]}")
            
            common_skills = [
                # Technical/Backend skills
                "python", "javascript", "react", "fastapi", "next.js", "docker", "postgres", "sql", "aws", "git", 
                "machine learning", "ml", "nlp", "kubernetes", "typescript", "data engineer", "spark", "hadoop", "airflow",
                # DevOps / SRE skills
                "terraform", "sre", "prometheus", "grafana", "kubernetes", "ansible", "jenkins",
                # QA / Testing skills
                "selenium", "playwright", "testing", "qa", "automation",
                # Sales / Marketing skills
                "sales", "prospect", "outreach", "crm", "hubspot", "salesforce", "negotiation", "marketing", "content", "b2b",
                "client", "lead", "leads", "proposal", "proposals",
                # Finance skills
                "excel", "sheets", "modeling", "forecasting", "budget", "finance", "financial", "accounting", "fpa",
                # HR / Talent skills
                "hr", "recruitment", "headcount", "relations", "recruiting", "employee", "hiring"
            ]
            
            # Group keywords into domains to calculate partial scores
            domains = {
                "technical": ["python", "javascript", "react", "fastapi", "next.js", "docker", "postgres", "sql", "aws", "git", "typescript", "data engineer", "spark", "hadoop", "airflow", "terraform", "sre", "prometheus", "grafana", "ansible", "jenkins", "kubernetes", "selenium", "playwright", "testing", "qa", "automation"],
                "sales_marketing": ["sales", "prospect", "outreach", "crm", "hubspot", "salesforce", "negotiation", "marketing", "content", "b2b", "client", "lead", "leads", "proposal", "proposals"],
                "finance": ["excel", "sheets", "modeling", "forecasting", "budget", "finance", "financial", "accounting", "fpa"],
                "hr": ["hr", "recruitment", "headcount", "relations", "recruiting", "employee", "hiring"]
            }

            matched = []
            missing = []
            
            for skill in common_skills:
                if skill in jd_text:
                    if skill in resume_text:
                        matched.append(skill.upper() if len(skill) <= 4 else skill.title())
                    else:
                        missing.append(skill.upper() if len(skill) <= 4 else skill.title())
            
            total = len(matched) + len(missing)
            exact_score = (len(matched) / total) if total > 0 else 0.0
            
            # Domain detection
            resume_is_tech = any(s in resume_text for s in domains["technical"])
            jd_is_tech = any(s in jd_text for s in domains["technical"])
            resume_is_sales = any(s in resume_text for s in domains["sales_marketing"])
            jd_is_sales = any(s in jd_text for s in domains["sales_marketing"])
            
            # Baseline domain scoring adjustments to give realistic numbers between 0% and 100%
            if jd_is_tech and resume_is_tech:
                score = max(0.55, exact_score)
            elif jd_is_sales and resume_is_sales:
                score = max(0.55, exact_score)
            else:
                score = exact_score * 0.5
                
            if total == 0:
                score = 0.50
                
            # Round score to two decimal places
            score = round(min(1.0, max(0.0, score)), 2)
            
            if score >= 0.75:
                rec = "shortlist"
                reason = f"Excellent technical stack and domain alignment with {score*100:.0f}% match."
                gap = f"Missing {', '.join(missing) or 'None'}."
                recommendation_text = "Candidate shortlisted for interview."
            elif score >= 0.45:
                rec = "hold"
                reason = f"Candidate has moderate domain alignment ({score*100:.0f}% match) but lacks key skills."
                gap = f"Missing {', '.join(missing) or 'None'}."
                recommendation_text = "Place candidate on hold for future review."
            else:
                rec = "archive"
                reason = f"Low compatibility ({score*100:.0f}% match) with critical job requirements."
                gap = f"Missing {', '.join(missing) or 'None'}."
                recommendation_text = "Archive candidate profile."

            summary = f"Reason: {reason}\nGap: {gap}\nRecommendation: {recommendation_text}"
                
            logger.info(f"[ResumeScreeningResult MOCK] score: {score}, recommendation: {rec}, summary: {summary}")
            
            mock_fields = {
                "match_score": score,
                "skill_matches": matched,
                "missing_skills": missing,
                "recommendation": rec,
                "summary": summary
            }
            try:
                val_res = schema.model_validate(mock_fields)
                logger.info(f"[ResumeScreeningResult MOCK] model_validate succeeded: {val_res}")
                return val_res
            except Exception as ex:
                logger.warning(f"[ResumeScreeningResult MOCK] model_validate failed: {ex}. Using model_construct.")
                return schema.model_construct(**mock_fields)

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
                mock_fields[name] = self._generate_mock_schema_data(field_type, messages)
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
