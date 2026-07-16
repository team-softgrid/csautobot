import os
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings


def get_embedding_function() -> Embeddings:
    """Return the embedding model used for dense RAG query/index.

    Production Chroma (`chroma_db_20260715_*`) was built with Ollama
    `nomic-embed-text` (768-d). Query embeddings must match that index.

    Default is Ollama (`USE_OLLAMA_EMBEDDING` unset or true). Set
    USE_OLLAMA_EMBEDDING=false only when the index was built with OpenAI
    text-embedding-3-small.
    """
    # Default "true" — .env에서 키가 빠져도 OpenAI 쿼터/차원 불일치로 BM25 폴백되지 않게 함.
    use_ollama = os.environ.get("USE_OLLAMA_EMBEDDING", "true").lower() == "true"
    if use_ollama:
        model = (os.environ.get("OLLAMA_EMBED_MODEL") or "nomic-embed-text").strip()
        base_url = (os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")
        return OllamaEmbeddings(model=model, base_url=base_url)
    return OpenAIEmbeddings(model="text-embedding-3-small")

