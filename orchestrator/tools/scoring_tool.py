from pydantic import BaseModel, Field
from orchestrator.groq_client import groq_client
from shared.utils.logging import get_logger

logger = get_logger(__name__)

class ResumeScreeningResult(BaseModel):
    match_score: float = Field(..., description="Calculated matching score between 0.0 and 1.0 (or 0 and 100 scaled)")
    skill_matches: list[str] = Field(default_factory=list, description="List of matching skills")
    missing_skills: list[str] = Field(default_factory=list, description="Skills listed in job requirements but missing from resume")
    recommendation: str = Field(..., description="Must be one of: 'shortlist', 'archive', 'hold'")
    summary: str = Field(..., description="Short summary justification for the decision")

class LeadScoringResult(BaseModel):
    close_probability: float = Field(..., description="Probability of closing the deal, between 0.0 and 1.0")
    key_drivers: list[str] = Field(default_factory=list, description="Primary reasons driving this score")
    recommended_tier: str = Field(..., description="Pricing tier: 'Enterprise', 'Standard', 'Basic'")
    estimated_deal_value: float = Field(..., description="Estimated contract value in USD")

def score_resume(resume_text: str, job_requirements: str) -> ResumeScreeningResult:
    """Uses Groq structured chat to screen and score a resume against job requirements."""
    logger.info("Executing resume scoring tool...")
    
    system_prompt = (
        "You are an expert HR recruiter. Read the candidate's resume and screen it against the job requirements. "
        "Calculate a match score between 0.0 and 1.0 (with 1.0 being perfect). Identify matching skills, missing "
        "skills, give a recommendation ('shortlist', 'archive', 'hold'), and write a brief summary."
    )
    
    user_prompt = f"### Job Requirements:\n{job_requirements}\n\n### Resume Text:\n{resume_text}"
    messages = [{"role": "user", "content": user_prompt}]
    
    try:
        result = groq_client.structured_chat(
            messages=messages,
            system_prompt=system_prompt,
            response_schema=ResumeScreeningResult
        )
        return result
    except Exception as e:
        logger.error(f"Error scoring resume: {e}")
        # Return fallback result
        return ResumeScreeningResult(
            match_score=0.5,
            skill_matches=[],
            missing_skills=[],
            recommendation="hold",
            summary=f"Fallback generated due to scoring error: {e}"
        )

def score_lead(needs_summary: str, budget_range: str) -> LeadScoringResult:
    """Uses Groq structured chat to score a sales lead based on needs and budget."""
    logger.info("Executing lead scoring tool...")
    
    system_prompt = (
        "You are a sales scoring engine. Based on the client needs and budget range, evaluate the deal "
        "probability (close_probability between 0.0 and 1.0), identify key drivers of the score, "
        "recommend a pricing tier ('Enterprise', 'Standard', 'Basic'), and estimate the deal value in USD."
    )
    
    user_prompt = f"### Customer Needs Summary:\n{needs_summary}\n\n### Budget Range:\n{budget_range}"
    messages = [{"role": "user", "content": user_prompt}]
    
    try:
        result = groq_client.structured_chat(
            messages=messages,
            system_prompt=system_prompt,
            response_schema=LeadScoringResult
        )
        return result
    except Exception as e:
        logger.error(f"Error scoring lead: {e}")
        # Parse a guess from the budget range for estimated value
        est_val = 10000.0
        try:
            if "-" in budget_range:
                parts = [p.strip().replace("$", "").replace(",", "") for p in budget_range.split("-")]
                est_val = float(parts[1])
        except Exception:
            pass
            
        return LeadScoringResult(
            close_probability=0.5,
            key_drivers=["Fallback default score due to processing error"],
            recommended_tier="Standard",
            estimated_deal_value=est_val
        )
