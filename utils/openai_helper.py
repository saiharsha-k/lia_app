# utils/openai_helper.py

import os
from langchain_openai import ChatOpenAI
from utils.config import OPENAI_API_KEY

def get_openai_llm(model: str = "gpt-4.1", temperature: float = 0.7) -> ChatOpenAI:
    """
    Initialize and return an OpenAI Chat model instance.
    Defaults to GPT-4.
    """
    return ChatOpenAI(
        model=model,
        api_key=OPENAI_API_KEY,
        temperature=temperature
    )
