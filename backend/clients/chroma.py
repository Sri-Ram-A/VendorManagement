# filepath: backend/clients/chroma.py
"""
Centralized vector management module using ChromaDB.
Handles semantic text segmentation, embedding generation, and ordered index storage.
"""

import uuid
import chromadb
from chromadb.utils import embedding_functions
from django.conf import settings
from backend.logging import get_vendor_logger


class VendorVectorStoreManager:
    """Manages local vector store operations using a persistent ChromaDB instance."""

    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(path=settings.CHROMA_DATA_PATH)
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

    def get_vendor_collection(self, vendor_id: str) -> chromadb.Collection:
        """Resolves isolated collection namespace targets securely using the unique vendor ID identifier."""
        collection_name = f"vendor_{vendor_id.replace('-', '_')}"
        return self.client.get_or_create_collection(
            name=collection_name, embedding_function=self.embedding_function
        )

    def vectorize_markdown_content(
        self, vendor_id: str, document_type: str, markdown_text: str
    ) -> None:
        """
        Splits raw markdown into sequential blocks, preserves critical numeric lines,
        and saves chunks with index tracking data.
        """
        v_logger = get_vendor_logger(vendor_id=vendor_id)
        collection = self.get_vendor_collection(vendor_id)

        #  1.1: TEXT SEGMENTATION ENGINE
        raw_paragraphs = markdown_text.split("\n\n")
        cleaned_chunks = []

        for paragraph in raw_paragraphs:
            text = paragraph.strip()
            # [CRITICAL: METRIC EXCLUSION PROTECTION
            # Retain short lines if they contain labels or numbers (e.g., "Level: 1" or "SLA: 99.9%")
            if len(text) > 40 or (
                len(text) > 4 and (":" in text or any(char.isdigit() for char in text))
            ):
                cleaned_chunks.append(text)

        if not cleaned_chunks:
            v_logger.warning(
                f"Exiting: '{document_type}' contained no valid text blocks."
            )
            return

        #  1.2: BATCH DATA STRUCTURING
        documents_batch = []
        metadata_batch = []
        identity_batch = []

        for index, block in enumerate(cleaned_chunks):
            documents_batch.append(block)
            # [CRITICAL: CHUNK SEQUENCE TRACKING
            # Storing chunk_index enables sorting chronologically when reading from the database
            metadata_batch.append(
                {"source_document_type": document_type, "chunk_index": index}
            )
            identity_batch.append(
                f"chunk_{document_type}_{index}_{uuid.uuid4().hex[:6]}"
            )

        #  1.3: PERSISTENT CHROMADB SYNC
        collection.add(
            documents=documents_batch, metadatas=metadata_batch, ids=identity_batch
        )
        v_logger.info(f"Vectorization finalized. Saved {len(cleaned_chunks)} vectors")

    def read_document_chunks_in_order(self, vendor_id: str, document_type: str) -> str:
        """
        Reads back every chunk belonging to one document type from this vendor's
        collection, sorted by chunk_index, and joins them into one markdown string.
        Returns an empty string if no chunks exist for this document type.
        """
        collection = self.get_vendor_collection(vendor_id)
        doc_data = collection.get(where={"source_document_type": document_type})
        chunks_with_idx = [
            (meta.get("chunk_index", 0), text)
            for text, meta in zip(
                doc_data.get("documents", []), doc_data.get("metadatas", [])
            )
        ]
        chunks_with_idx.sort(key=lambda pair: pair[0])

        return "\n\n".join(text for _, text in chunks_with_idx)


_vector_store = None


def get_vector_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = VendorVectorStoreManager()
    return _vector_store
