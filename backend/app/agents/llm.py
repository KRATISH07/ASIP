"""
LLM factory: returns the configured LangChain chat model.
Reads LLM_PROVIDER from settings to switch between OpenAI and Google Gemini.
"""
from functools import lru_cache
from app.config import settings


@lru_cache()
def get_llm(temperature: float = 0.1):
    if settings.llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.google_api_key,
            temperature=temperature,
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            temperature=temperature,
        )


@lru_cache()
def get_embedding_model():
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )
