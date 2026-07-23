import pytest
from unittest.mock import patch
from app.agents.llm import get_llm
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings


def test_openai_model_routing():
    get_llm.cache_clear()

    with (
        patch("app.config.settings.llm_provider", "openai"),
        patch("app.config.settings.llm_model", "gpt-4o"),
        patch("app.config.settings.openai_api_key", "fake-key")
    ):
        # 1. Extraction/Notification -> gpt-4o-mini
        llm_extract = get_llm(task_type="extraction")
        assert isinstance(llm_extract, ChatOpenAI)
        assert llm_extract.model_name == "gpt-4o-mini"

        llm_notif = get_llm(task_type="notification", temperature=0.3)
        assert isinstance(llm_notif, ChatOpenAI)
        assert llm_notif.model_name == "gpt-4o-mini"
        assert llm_notif.temperature == pytest.approx(0.3)

        # 2. Diagnosis/Supervisor/General -> settings.llm_model (gpt-4o)
        llm_diag = get_llm(task_type="diagnosis")
        assert isinstance(llm_diag, ChatOpenAI)
        assert llm_diag.model_name == "gpt-4o"

        llm_super = get_llm(task_type="supervisor")
        assert isinstance(llm_super, ChatOpenAI)
        assert llm_super.model_name == "gpt-4o"

        llm_gen = get_llm(task_type="general")
        assert isinstance(llm_gen, ChatOpenAI)
        assert llm_gen.model_name == "gpt-4o"


def test_gemini_model_routing():
    get_llm.cache_clear()

    with (
        patch("app.config.settings.llm_provider", "google"),
        patch("app.config.settings.gemini_model", "gemini-1.5-pro"),
        patch("app.config.settings.google_api_key", "fake-key")
    ):
        # 1. Extraction/Notification -> gemini-1.5-flash
        llm_extract = get_llm(task_type="extraction")
        assert isinstance(llm_extract, ChatGoogleGenerativeAI)
        assert llm_extract.model in ("gemini-1.5-flash", "models/gemini-1.5-flash")

        # 2. Diagnosis/Supervisor/General -> settings.gemini_model (gemini-1.5-pro)
        llm_diag = get_llm(task_type="diagnosis")
        assert isinstance(llm_diag, ChatGoogleGenerativeAI)
        assert llm_diag.model in ("gemini-1.5-pro", "models/gemini-1.5-pro")
