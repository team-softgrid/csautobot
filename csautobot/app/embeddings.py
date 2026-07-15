import os
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings

def get_embedding_function() -> Embeddings:
    use_ollama = os.environ.get("USE_OLLAMA_EMBEDDING", "false").lower() == "true"
    if use_ollama:
        return OllamaEmbeddings(model="nomic-embed-text")
    else:
        return OpenAIEmbeddings(model="text-embedding-3-small")

