"""
LLM factory: returns the configured LangChain chat model.
Reads LLM_PROVIDER from settings to switch between OpenAI and Google Gemini.
"""
from functools import lru_cache
from app.config import settings


@lru_cache(maxsize=32)
def get_llm(task_type: str = "general", temperature: float = 0.1):
    if settings.llm_provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        model_map = {
            "extraction": "gemini-1.5-flash",
            "notification": "gemini-1.5-flash",
            "diagnosis": settings.gemini_model,
            "supervisor": settings.gemini_model,
            "general": settings.gemini_model,
        }
        model_name = model_map.get(task_type, settings.gemini_model)
        api_key = settings.google_api_key or "mock-google-key"
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=temperature,
        )
    else:
        from langchain_openai import ChatOpenAI
        model_map = {
            "extraction": "gpt-4o-mini",
            "notification": "gpt-4o-mini",
            "diagnosis": settings.llm_model,
            "supervisor": settings.llm_model,
            "general": settings.llm_model,
        }
        model_name = model_map.get(task_type, settings.llm_model)
        api_key = settings.openai_api_key or "mock-openai-key"
        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            temperature=temperature,
        )


@lru_cache()
def get_embedding_model():
    from langchain_openai import OpenAIEmbeddings
    api_key = settings.openai_api_key or "mock-openai-key"
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=api_key,
    )
