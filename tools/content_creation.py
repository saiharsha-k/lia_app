from typing import Optional, Dict
from pydantic import BaseModel
from langchain_core.tools import StructuredTool
from tools.content_research import web_content_research
from utils.openai_helper import get_openai_llm  # Importing the helper function

# LLM initialization using the helper function
llm = get_openai_llm(model="gpt-4", temperature=0.7)

# Argument schema for structured tool
class ContentCreationArgs(BaseModel):
    content_type: str
    topic: str
    summary: Optional[str] = None  # Now optional
    feedback: Optional[str] = None

# Actual tool function
def content_creation_tool(
    content_type: str,
    topic: str,
    summary: Optional[str] = None,
    feedback: Optional[str] = None
) -> Dict[str, str]:
    try:
        # Auto research if summary is missing
        if not summary or summary.strip() == "":
            research_result = web_content_research.invoke({"topic": topic})
            summary = research_result.get("summary", "")

        prompt = f"""
        Create a LinkedIn {content_type} about: {topic}

        Research Summary:
        {summary}

        {"User Feedback to Incorporate: " + feedback if feedback else ""}

        Guidelines:
        - Post: 100-300 chars, engaging hook, 1-2 key points
        - Article: 300+ words, clear sections, examples
        - Include relevant hashtags
        - Use professional but approachable tone
        """

        # Use the OpenAI model (via LangChain) for completion
        response = llm.invoke(prompt)
        
        return {
            "content": response.content,
            "status": "success",
            "type": content_type
        }

    except Exception as e:
        return {
            "content": str(e),
            "status": "error"
        }

# Register as structured tool
content_creation_structured_tool = StructuredTool.from_function(
    func=content_creation_tool,
    name="content_creation",
    description="Create LinkedIn content (post or article). Requires content_type and topic. Auto-researches if no summary is provided.",
    args_schema=ContentCreationArgs
)
