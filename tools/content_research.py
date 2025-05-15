import requests
from langchain_core.tools import tool
from typing import Dict, List
import json
import logging
from urllib.parse import quote_plus
from utils.config import SERPAPI_KEY  # Now using SerpAPI key
from utils.openai_helper import get_openai_llm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize LLM
llm = get_openai_llm(model="gpt-4.1", temperature=0.7)

@tool
def web_content_research(query: str) -> Dict[str, List]:
    """
    Research web content and return structured data including:
    - Key insights (summary)
    - Framework comparisons
    - Use cases
    - Top sources
    
    Args:
        query: The search query (e.g., "Libraries & Frameworks for AI Agents")
    
    Returns:
        Dictionary with:
        - 'summary': Concise overview
        - 'comparisons': List of framework comparisons
        - 'use_cases': List of practical applications
        - 'sources': List of source URLs
        - 'error': (if any) Error message
    """
    try:
        # 1. Perform search using SerpAPI
        search_results = _serpapi_search(query)
        if not search_results:
            raise ValueError("No search results found")
        
        # 2. Process and analyze results
        research_data = {
            "summary": "",
            "comparisons": [],
            "use_cases": [],
            "sources": [r["link"] for r in search_results],
            "error": None
        }
        
        # 3. Extract and analyze content from top 3 results
        content_to_analyze = []
        for result in search_results[:3]:
            try:
                content = _get_page_content(result["link"])
                if content:
                    content_to_analyze.append({
                        "title": result["title"],
                        "content": content
                    })
            except Exception as e:
                logger.warning(f"Error processing {result['link']}: {str(e)}")
                continue
        
        # 4. Generate comprehensive analysis
        if content_to_analyze:
            analysis = _generate_analysis(query, content_to_analyze)
            research_data.update(analysis)
        
        # 5. Create final summary if none generated
        if not research_data["summary"]:
            snippets = [f"{r['title']}: {r['snippet']}" for r in search_results[:3]]
            research_data["summary"] = _generate_summary(query, "\n\n".join(snippets))
        
        return research_data
        
    except Exception as e:
        logger.error(f"Research failed: {str(e)}")
        return {
            "summary": "",
            "comparisons": [],
            "use_cases": [],
            "sources": [],
            "error": str(e)
        }

def _serpapi_search(query: str) -> List[Dict]:
    """Perform search using SerpAPI"""
    try:
        params = {
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 5,
            "hl": "en",
            "gl": "us"
        }
        response = requests.get(
            "https://serpapi.com/search.json",
            params=params,
            timeout=15
        )
        response.raise_for_status()
        
        return [
            {
                "title": r.get("title"),
                "link": r.get("link"),
                "snippet": r.get("snippet")
            }
            for r in response.json().get("organic_results", [])
        ]
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise Exception(f"Search API error: {str(e)}")

def _get_page_content(url: str) -> str:
    """Extract main content from webpage"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Use readability-lxml or similar in production for better extraction
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Simple content extraction
        main = soup.find('main') or soup.find('article') or soup
        return ' '.join(p.get_text().strip() for p in main.find_all('p'))
    except Exception as e:
        logger.warning(f"Content extraction failed for {url}: {str(e)}")
        return ""

def _generate_analysis(topic: str, contents: List[Dict]) -> Dict:
    """Generate structured analysis using LLM"""
    try:
        prompt = f"""Analyze these documents about {topic} and extract:
        1. Comprehensive summary (3-5 key points)
        2. Framework comparisons (name1, name2, pros, cons)
        3. Practical use cases (framework, scenario, example)
        
        Documents:
        {json.dumps(contents, indent=2)}
        
        Return JSON with: summary, comparisons, use_cases"""
        
        response = llm.invoke(prompt)
        return json.loads(response.content)
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return {}

def _generate_summary(topic: str, content: str) -> str:
    """Fallback summary generation"""
    prompt = f"""Create a 6-7 point summary about {topic} from this content:
    {content[:10000]}
    
    Focus on key insights for technical professionals."""
    
    response = llm.invoke(prompt)
    return response.content