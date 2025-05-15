# trend_research_tool.py
from utils.openai_helper import get_openai_llm  # Import OpenAI helper
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from typing import Annotated
from utils.config import OPENAI_API_KEY  # Can be replaced with your OpenAI API key or use environment variable

from bs4 import BeautifulSoup
import requests
from typing import Dict, Tuple
import json

class TrendResearchTool:
    def __init__(self):
        self.llm = get_openai_llm(model="gpt-4", temperature=0.7)  # Use OpenAI GPT-4
        self.search_url = "https://www.google.com/search?q=site:linkedin.com+{query}&tbm=nws"

    def get_trend_analysis(self, industry: str) -> Dict[str, str]:
        """Get trends with content recommendations"""
        try:
            # 1. Fetch raw trends
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(
                self.search_url.format(query=f"{industry} trends"),
                headers=headers,
                timeout=10
            )
            soup = BeautifulSoup(response.text, 'html.parser')
            raw_trends = [h.text for h in soup.find_all('h3')[:5]]
            trends_list = "\n".join(f"- {trend}" for trend in raw_trends)

            # 2. Create analysis prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You're a LinkedIn content strategist analyzing trends."),
                ("human", """
                Industry: {industry}
                Current Trends:
                {trends_list}

                Provide:
                1. A 1-paragraph summary of key insights
                2. Bullet points of content ideas (3-5)
                3. JSON data with:
                   - top_trends (array)
                   - engagement_potential (low/medium/high)

                Format:
                Summary: <paragraph>
                Content Ideas:
                - <idea1>
                - <idea2>
                
                Data: ```json
                <json_data>
                ```
                """)
            ])

            # 3. Get analysis
            chain = prompt | self.llm
            result = chain.invoke({
                "industry": industry,
                "trends_list": trends_list
            })

            # 4. Parse response
            response = result.content if hasattr(result, 'content') else str(result)
            
            # Extract components
            summary = self._extract_section("Summary:", "Content Ideas:", response)
            content_ideas = self._extract_bullets(response)
            json_data = self._extract_json(response)

            return {
                "summary": summary,
                "content_ideas": content_ideas,
                "data": json_data
            }

        except Exception as e:
            return {"error": str(e)}

    def _extract_section(self, start: str, end: str, text: str) -> str:
        """Helper to extract text between markers"""
        try:
            return text.split(start)[1].split(end)[0].strip()
        except:
            return ""

    def _extract_bullets(self, text: str) -> list:
        """Extract bullet points from response"""
        bullets = []
        in_section = False
        for line in text.split('\n'):
            if "Content Ideas:" in line:
                in_section = True
                continue
            if in_section and line.strip().startswith('-'):
                bullets.append(line.strip()[2:])
        return bullets

    def _extract_json(self, text: str) -> dict:
        """Extract JSON data from response"""
        try:
            json_str = text.split('```json')[1].split('```')[0].strip()
            return json.loads(json_str)
        except:
            return {}
        
@tool("trend_research_tool")
def trend_research(
    industry: Annotated[str, "The industry to research trends for (e.g., 'Artificial Intelligence')"]
) -> dict:
    """Research current LinkedIn trends and provide content recommendations for a specific industry."""
    analyzer = TrendResearchTool()  # No need for API key as OpenAI key is handled internally
    return analyzer.get_trend_analysis(industry)
