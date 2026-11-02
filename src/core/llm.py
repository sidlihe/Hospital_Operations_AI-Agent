
from langchain_groq import ChatGroq
from src.config import settings


def get_llm(temperature: float = 0.0) -> ChatGroq:
    return ChatGroq(
        model=settings.LLM_MODEL,
        temperature=temperature,
        api_key=settings.GROQ_API_KEY,
    )
