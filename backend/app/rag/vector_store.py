"""
ChromaDB vector store client for ASIP RAG system.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings
from app.core.logging import get_logger

logger = get_logger("vector_store")

_chroma_client = None
_collection = None


def get_chroma_client() -> chromadb.HttpClient:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        logger.info("ChromaDB client initialized", host=settings.chroma_host)
    return _chroma_client


def get_collection():
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB collection ready", name=settings.chroma_collection_name)
    return _collection
