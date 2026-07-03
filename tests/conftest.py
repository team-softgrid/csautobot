import os
import sys
from pathlib import Path

import pytest

# 테스트 시 실제 API 키 사용 방지
os.environ.setdefault("OPENAI_API_KEY", "sk-mock-key-for-testing")
os.environ.setdefault("ANTHROPIC_API_KEY", "mock-anthropic-key")
os.environ.setdefault("GOOGLE_API_KEY", "mock-google-key")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("CHROMA_DB_PATH", ":memory:")

# csautobot 패키지 경로 추가
ROOT = Path(__file__).resolve().parent.parent
CSAUTOBOT = ROOT / "csautobot"
for p in [str(ROOT), str(CSAUTOBOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(scope="session")
def app():
    """FastAPI 앱을 테스트용으로 초기화합니다."""
    from csautobot.main import app as _app
    return _app


@pytest.fixture(scope="session")
def client(app):
    """TestClient를 반환합니다."""
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def mock_llm(mocker):
    """LLM 호출을 Mock하여 실제 API를 사용하지 않습니다."""
    mock = mocker.MagicMock()
    mock.invoke.return_value = mocker.MagicMock(content="Mock LLM 응답입니다.")
    mocker.patch("langchain_openai.ChatOpenAI", return_value=mock)
    mocker.patch("langchain_anthropic.ChatAnthropic", return_value=mock) if _safe_import("langchain_anthropic") else None
    return mock


@pytest.fixture(autouse=True)
def mock_chroma(mocker):
    """ChromaDB를 Mock합니다."""
    mock_db = mocker.MagicMock()
    mock_db.similarity_search.return_value = []
    mock_db.similarity_search_with_relevance_scores.return_value = []
    mocker.patch("langchain_chroma.Chroma", return_value=mock_db)
    return mock_db


def _safe_import(module: str) -> bool:
    try:
        __import__(module)
        return True
    except ImportError:
        return False
