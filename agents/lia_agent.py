from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import Tool
from utils.openai_helper import get_openai_llm  # Import OpenAI helper

from tools.trend_research import trend_research
from tools.content_research import web_content_research
from tools.content_creation import content_creation_structured_tool
from tools.scheduling_tool import scheduling_structured_tool, check_schedule_structured_tool  # Import the new check schedule tool
from tools.posting_tool import post_content_to_linkedin  # Make sure this is correct path

import json

class LinkedInAgent:
    def __init__(self, api_key: str = ""):
        # Initialize OpenAI LLM (GPT-4)
        self.llm = get_openai_llm(model="gpt-4.1", temperature=0.6)

        # Registering the tools
        self.tools = [
            Tool(
                name="trend_research",
                func=trend_research.invoke,
                description="Research LinkedIn trends for specific industries."
            ),
            Tool(
                name="content_research",
                func=web_content_research.invoke,
                description="Research and summarize web content about a topic. Returns structured research summary."
            ),
            content_creation_structured_tool,
            scheduling_structured_tool,
            check_schedule_structured_tool,  # Add the new tool to the tools list
            Tool(
                name="post_content_to_linkedin",
                func=post_content_to_linkedin.invoke,
                description="Posts a given record ID from Airtable to LinkedIn. Accepts record_id and optional immediate flag."
            )
        ]

        # In-memory conversation log
        self.chat_history = []

        # Load the character.json instructions and integrate them into the system message
        with open("agents/character.json", "r") as file:
            character_data = json.load(file)

        # Combine the relevant parts into a readable text block
        character_instructions = f"""
        {character_data['character_description']}

        Role:
        {character_data['role']}

        Responsibilities:
        - {"\n- ".join(character_data['responsibilities'])}

        Standard Operating Procedure (SOP):
        - {"\n- ".join(character_data['SOP'])}

        Behavior Guidelines:
        - {"\n- ".join(character_data['behavior_instructions'])}

        Tools Available:
        {chr(10).join([f"- {tool['name']}: {tool['description']}" for tool in character_data['tools_available']])}
        """

        # Create the agent
        self.agent = self._create_agent(character_instructions, character_name="Lia")

    def _create_agent(self, character_instructions: str, character_name: str = "Lia") -> AgentExecutor:
    # Compose a full system prompt
        full_system_prompt = f"""{character_name} is a skilled LinkedIn content creator agent.

    {character_instructions}

    You can handle tasks such as:
    - Creating posts or articles for LinkedIn
    - Researching trending topics
    - Scheduling content
    - Checking scheduled content

    Use appropriate tools when needed. Always write in a clear, sharp, professional style. Include insights and hashtags when applicable.
    """

        prompt = ChatPromptTemplate.from_messages([
            ("system", full_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=15,
            handle_parsing_errors=True
        )

    def run(self, query: str) -> str:
        try:
            # Add current user input to chat history
            self.chat_history.append(HumanMessage(content=query))

            # Invoke the agent with the query
            response = self.agent.invoke({
                "input": query,
                "chat_history": self.chat_history
            })

            # Add model response to chat history
            self.chat_history.append(AIMessage(content=response["output"]))
            return response["output"]

        except Exception as e:
            return f"Error: {str(e)}"
