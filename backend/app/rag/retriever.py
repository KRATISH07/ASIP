"""
RAG Retriever — wraps ChromaDB with LangChain's retriever interface.
Used by InfrastructureAgent and ContractorAgent for context injection.
"""
from functools import lru_cache
from langchain_chroma import Chroma
from app.agents.llm import get_embedding_model
from app.config import settings
from app.core.logging import get_logger
import chromadb.config

logger = get_logger("retriever")


@lru_cache()
def get_retriever(k: int = 3):
    """Returns a LangChain retriever backed by ChromaDB."""
    embeddings = get_embedding_model()
    # Build chromadb Settings instance from config dict
    client_settings = chromadb.config.Settings(
        chroma_server_host=settings.chroma_host,
        chroma_server_http_port=int(settings.chroma_port) if settings.chroma_port is not None else None,
    )

    vectorstore = Chroma(
        collection_name=settings.chroma_collection_name,
        embedding_function=embeddings,
        client_settings=client_settings,
    )
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )


async def ingest_documents(docs_path: str) -> int:
    """
    Load, chunk, embed and store documents from a directory.
    Returns number of chunks stored.
    """
    from langchain_community.document_loaders import DirectoryLoader, TextLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_chroma import Chroma

    logger.info("Starting document ingestion", path=docs_path)

    loader = DirectoryLoader(docs_path, glob="**/*.txt", loader_cls=TextLoader)
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_documents(documents)

    embeddings = get_embedding_model()
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=settings.chroma_collection_name,
        client_settings=chromadb.config.Settings(
            chroma_server_host=settings.chroma_host,
            chroma_server_http_port=int(settings.chroma_port) if settings.chroma_port is not None else None,
        ),
    )

    logger.info("Ingestion complete", chunks=len(chunks), source_docs=len(documents))
    return len(chunks)
