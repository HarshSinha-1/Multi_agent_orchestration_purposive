from mcp.notion_mcp_client import NotionMCPClient
from mcp.config import NOTION_DATABASE_ID
from shared.utils.logging import get_logger
from datetime import datetime
from typing import Optional

logger = get_logger(__name__)

# Singleton instance of Notion MCP Client
mcp_client = NotionMCPClient()

def sync_job_to_notion(job) -> dict:
    """
    Syncs a Job record to Notion using the Notion MCP Client.
    Follows the idempotency rule: updates the page if notion_page_id is present,
    otherwise creates a new page and returns the notion_page_id.
    """
    properties = {
        "job_id": {
            "title": [
                {
                    "text": {
                        "content": job.job_id
                    }
                }
            ]
        },
        "job_title": {
            "rich_text": [
                {
                    "text": {
                        "content": job.title
                    }
                }
            ]
        },
        "department": {
            "select": {
                "name": job.department if job.department else "General"
            }
        },
        "full_jd_text": {
            "rich_text": [
                {
                    "text": {
                        # Limit to 2000 chars to satisfy Notion API limits
                        "content": job.full_jd_text[:2000] if job.full_jd_text else ""
                    }
                }
            ]
        },
        "created_at": {
            "date": {
                "start": job.created_at.strftime("%Y-%m-%d") if isinstance(job.created_at, datetime) else datetime.utcnow().strftime("%Y-%m-%d")
            }
        }
    }

    try:
        if job.notion_page_id:
            # Idempotency rule: update existing page properties
            logger.info(f"Syncing existing Job {job.job_id} to Notion page {job.notion_page_id}")
            result = mcp_client.call_tool(
                "notion_update_page_properties",
                {
                    "page_id": job.notion_page_id,
                    "properties": properties
                }
            )
            return {"status": "updated", "page_id": job.notion_page_id, "url": result.get("url")}
        else:
            # Idempotency rule: create a new page in the database
            logger.info(f"Creating new Notion page for Job {job.job_id} in Database {NOTION_DATABASE_ID}")
            result = mcp_client.call_tool(
                "notion_create_page",
                {
                    "parent": {"database_id": NOTION_DATABASE_ID},
                    "properties": properties
                }
            )
            page_id = result.get("id")
            url = result.get("url")
            return {"status": "created", "page_id": page_id, "url": url}
    except Exception as e:
        logger.error(f"Failed to sync Job {job.job_id} to Notion: {e}")
        return {"status": "failed", "error": str(e)}

def sync_candidate_to_notion(candidate, database_id: str = None) -> dict:
    """
    Syncs a Candidate record to Notion. If database_id is not specified,
    uses the main NOTION_DATABASE_ID.
    """
    db_id = database_id or NOTION_DATABASE_ID
    
    properties = {
        "candidate_id": {
            "title": [
                {
                    "text": {
                        "content": candidate.candidate_id
                    }
                }
            ]
        },
        "name": {
            "rich_text": [
                {
                    "text": {
                        "content": candidate.name
                    }
                }
            ]
        },
        "job_id": {
            "rich_text": [
                {
                    "text": {
                        "content": candidate.job_id
                    }
                }
            ]
        },
        "match_score": {
            "number": float(candidate.match_score)
        },
        "skills": {
            "rich_text": [
                {
                    "text": {
                        "content": candidate.skills[:2000] if candidate.skills else ""
                    }
                }
            ]
        },
        "missing_skills": {
            "rich_text": [
                {
                    "text": {
                        "content": candidate.missing_skills[:2000] if candidate.missing_skills else ""
                    }
                }
            ]
        },
        "recommendation": {
            "select": {
                "name": candidate.recommendation if candidate.recommendation else "review"
            }
        },
        "summary": {
            "rich_text": [
                {
                    "text": {
                        "content": candidate.summary[:2000] if candidate.summary else ""
                    }
                }
            ]
        }
    }

    try:
        if candidate.notion_page_id:
            logger.info(f"Syncing existing Candidate {candidate.candidate_id} to Notion page {candidate.notion_page_id}")
            result = mcp_client.call_tool(
                "notion_update_page_properties",
                {
                    "page_id": candidate.notion_page_id,
                    "properties": properties
                }
            )
            return {"status": "updated", "page_id": candidate.notion_page_id, "url": result.get("url")}
        else:
            logger.info(f"Creating new Notion page for Candidate {candidate.candidate_id} in Database {db_id}")
            result = mcp_client.call_tool(
                "notion_create_page",
                {
                    "parent": {"database_id": db_id},
                    "properties": properties
                }
            )
            page_id = result.get("id")
            url = result.get("url")
            return {"status": "created", "page_id": page_id, "url": url}
    except Exception as e:
        logger.error(f"Failed to sync Candidate {candidate.candidate_id} to Notion: {e}")
        return {"status": "failed", "error": str(e)}

def fetch_job_from_notion(job_id: str) -> Optional[dict]:
    """
    Queries Notion for a job description page matching job_id.
    Returns a dict with title, department, full_jd_text, and notion_page_id.
    """
    logger.info(f"Fetching job data from Notion for job_id: {job_id}")
    try:
        filter_payload = {
            "property": "job_id",
            "title": {
                "equals": job_id
            }
        }
        res = mcp_client.call_tool(
            "notion_query_database",
            {
                "database_id": NOTION_DATABASE_ID,
                "filter": filter_payload
            }
        )
        results = res.get("results", [])
        if not results:
            logger.warning(f"No job page found in Notion matching job_id: {job_id}")
            return None
        
        page = results[0]
        notion_page_id = page.get("id")
        props = page.get("properties", {})
        
        # In Notion, properties match confirmed schema: job_title, department, full_jd_text
        title_list = props.get("job_title", {}).get("rich_text", [])
        title = title_list[0].get("text", {}).get("content", "") if title_list else ""
        
        dept_obj = props.get("department", {}).get("select", {})
        department = dept_obj.get("name", "General") if dept_obj else "General"
        
        jd_list = props.get("full_jd_text", {}).get("rich_text", [])
        full_jd_text = jd_list[0].get("text", {}).get("content", "") if jd_list else ""
        
        return {
            "job_id": job_id,
            "title": title,
            "department": department,
            "full_jd_text": full_jd_text,
            "notion_page_id": notion_page_id
        }
    except Exception as e:
        logger.error(f"Failed to fetch job {job_id} from Notion: {e}")
        return None

