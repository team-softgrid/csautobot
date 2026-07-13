import os


def get_embedding_function():
    """RAG 벡터 검색용 임베딩 함수.

    서버에 상시 구동 중인 Ollama의 로컬 임베딩 모델(기본 bge-m3)을 사용한다.
    API 키/할당량이 필요 없어 OpenAI Embedding 할당량 초과로 인한
    BM25-only 강등 문제를 근본적으로 없앤다.
    모델/주소는 OLLAMA_EMBEDDING_MODEL / OLLAMA_EMBEDDING_BASE_URL로 재정의 가능.
    """
    try:
        from langchain_ollama import OllamaEmbeddings
    except ImportError:
        from langchain_community.embeddings import OllamaEmbeddings

    return OllamaEmbeddings(
        model=os.environ.get("OLLAMA_EMBEDDING_MODEL", "bge-m3"),
        base_url=os.environ.get("OLLAMA_EMBEDDING_BASE_URL", "http://localhost:11434"),
    )
