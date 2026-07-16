import os
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings


def get_embedding_function() -> Embeddings:
    """Return the embedding model used for dense RAG query/index.

    Production Chroma (`chroma_db_20260715_*`) was built with Ollama
    `nomic-embed-text` (768-d). If the process still uses OpenAI
    `text-embedding-3-small` (1536-d), dense search fails with quota/dim
    errors and the UI shows embedding_degraded even after re-indexing.

    Set USE_OLLAMA_EMBEDDING=true to match the Ollama-built index.
    """
    use_ollama = os.environ.get("USE_OLLAMA_EMBEDDING", "false").lower() == "true"
    if use_ollama:
        model = (os.environ.get("OLLAMA_EMBED_MODEL") or "nomic-embed-text").strip()
        base_url = (os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434").rstrip("/")
        return OllamaEmbeddings(model=model, base_url=base_url)
    return OpenAIEmbeddings(model="text-embedding-3-small")

