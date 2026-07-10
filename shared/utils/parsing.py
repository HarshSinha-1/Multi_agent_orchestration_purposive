import io
from pypdf import PdfReader
from shared.utils.logging import get_logger

logger = get_logger(__name__)

def parse_resume_text(file_bytes: bytes) -> str:
    """Parses a PDF resume file from bytes and extracts all text content."""
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Error parsing PDF resume: {e}")
        # Fallback to decoding as string if it's text
        try:
            return file_bytes.decode('utf-8', errors='ignore').strip()
        except Exception:
            return ""

def parse_log_lines(raw_text: str) -> list[str]:
    """Parses raw log text into a clean list of log lines, ignoring empty lines."""
    if not raw_text:
        return []
    return [line.strip() for line in raw_text.splitlines() if line.strip()]
