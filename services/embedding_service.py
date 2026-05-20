"""
Embedding Service for generating and managing embeddings
"""
from typing import List, Dict, Any
import logging
import hashlib
from datetime import datetime

from backend.services.llm_service import llm_service
from backend.services.vector_service import vector_service
from backend.app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for embedding generation and management"""
    
    def __init__(self):
        """Initialize embedding service"""
        self.llm_service = llm_service
        self.vector_service = vector_service
    
    def generate_document_id(self, content: str, url: str = "") -> str:
        """
        Generate unique ID for a document
        
        Args:
            content: Document content
            url: Document URL
            
        Returns:
            Unique document ID
        """
        # Create hash from content and URL
        hash_input = f"{url}:{content[:500]}"
        doc_id = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        return doc_id
    
    async def embed_document(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate embedding for a single document
        
        Args:
            content: Document content
            metadata: Document metadata (title, url, source_type, etc.)
            
        Returns:
            Document with embedding
        """
        try:
            logger.info(f"Generating embedding for document: {metadata.get('title', 'Unknown')}")
            
            # Generate embedding
            embedding = await self.llm_service.generate_embedding(content)
            
            # Generate document ID
            doc_id = self.generate_document_id(
                content=content,
                url=metadata.get("url", "")
            )
            
            # Add content to metadata for retrieval
            metadata["content"] = content
            metadata["embedded_at"] = datetime.utcnow().isoformat()
            metadata["chunk_size"] = len(content)
            
            return {
                "id": doc_id,
                "values": embedding,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error embedding document: {str(e)}")
            raise
    
    async def embed_documents_batch(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for multiple documents
        
        Args:
            documents: List of documents with content and metadata
            
        Returns:
            List of documents with embeddings
        """
        try:
            logger.info(f"Generating embeddings for {len(documents)} documents")
            
            # Filter out documents with empty content
            valid_documents = [doc for doc in documents if doc.get("content", "").strip()]
            
            if len(valid_documents) < len(documents):
                logger.warning(f"Filtered out {len(documents) - len(valid_documents)} documents with empty content")
            
            if not valid_documents:
                logger.error("No valid documents to embed after filtering")
                return []
            
            # Extract content for batch embedding
            contents = [doc["content"] for doc in valid_documents]
            
            # Generate embeddings in batch
            embeddings = await self.llm_service.generate_embeddings_batch(contents)
            
            # Combine embeddings with documents
            embedded_docs = []
            for i, doc in enumerate(valid_documents):
                doc_id = self.generate_document_id(
                    content=doc["content"],
                    url=doc.get("metadata", {}).get("url", "")
                )
                
                metadata = doc.get("metadata", {})
                metadata["content"] = doc["content"]
                metadata["embedded_at"] = datetime.utcnow().isoformat()
                metadata["chunk_size"] = len(doc["content"])
                
                embedded_docs.append({
                    "id": doc_id,
                    "values": embeddings[i],
                    "metadata": metadata
                })
            
            logger.info(f"Successfully generated {len(embedded_docs)} embeddings")
            
            return embedded_docs
            
        except Exception as e:
            logger.error(f"Error embedding documents batch: {str(e)}")
            raise
    
    async def ingest_documents(
        self,
        documents: List[Dict[str, Any]],
        namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Embed and ingest documents into vector database
        
        Args:
            documents: List of documents with content and metadata
            namespace: Optional namespace for organization
            
        Returns:
            Ingestion statistics
        """
        try:
            logger.info(f"Ingesting {len(documents)} documents")
            
            # Generate embeddings
            embedded_docs = await self.embed_documents_batch(documents)
            
            # Upsert to vector database
            result = await self.vector_service.upsert_vectors(
                vectors=embedded_docs,
                namespace=namespace
            )
            
            logger.info(f"Successfully ingested {result['upserted_count']} documents")
            
            return {
                "documents_processed": len(documents),
                "vectors_upserted": result["upserted_count"],
                "namespace": namespace,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error ingesting documents: {str(e)}")
            raise
    async def ingest_document(
        self,
        doc_id: str,
        text: str,
        metadata: Dict[str, Any],
        namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Ingest a single document into vector database
        
        Args:
            doc_id: Document ID
            text: Document text content
            metadata: Document metadata
            namespace: Optional namespace for organization
            
        Returns:
            Ingestion result
        """
        try:
            logger.info(f"Ingesting single document: {doc_id}")
            
            # Prepare document for ingestion
            document = {
                "content": text,
                "metadata": metadata
            }
            
            # Use the batch ingestion method
            result = await self.ingest_documents([document], namespace=namespace)
            
            return {
                "status": "success",
                "document_id": doc_id,
                "vectors_upserted": result["vectors_upserted"]
            }
            
        except Exception as e:
            logger.error(f"Error ingesting document {doc_id}: {str(e)}")
            raise
    
    
    async def search_similar(
        self,
        query: str,
        top_k: int = None,
        namespace: str = "",
        filter_dict: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using query text
        
        Args:
            query: Search query text
            top_k: Number of results to return
            namespace: Optional namespace to search in
            filter_dict: Optional metadata filter
            
        Returns:
            List of similar documents with scores
        """
        try:
            logger.info(f"Searching for: {query[:100]}...")
            
            # Generate query embedding
            query_embedding = await self.llm_service.generate_embedding(query)
            
            # Search vector database
            results = await self.vector_service.search(
                query_vector=query_embedding,
                top_k=top_k or settings.TOP_K_RESULTS,
                namespace=namespace,
                filter_dict=filter_dict
            )
            
            logger.info(f"Found {len(results)} similar documents")
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {str(e)}")
            raise
    
    async def delete_documents(
        self,
        document_ids: List[str],
        namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Delete documents from vector database
        
        Args:
            document_ids: List of document IDs to delete
            namespace: Optional namespace
            
        Returns:
            Deletion result
        """
        try:
            logger.info(f"Deleting {len(document_ids)} documents")
            
            result = await self.vector_service.delete_vectors(
                ids=document_ids,
                namespace=namespace
            )
            
            logger.info(f"Successfully deleted {result['deleted_count']} documents")
            
            return result
            
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            raise
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get embedding and vector database statistics
        
        Returns:
            Statistics dictionary
        """
        try:
            stats = await self.vector_service.get_index_stats()
            
            return {
                "total_documents": stats["total_vector_count"],
                "index_dimension": stats["dimension"],
                "index_fullness": stats["index_fullness"],
                "namespaces": stats["namespaces"],
                "embedding_model": settings.EMBEDDING_MODEL,
                "chunk_size": settings.CHUNK_SIZE
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            raise


# Global instance
embedding_service = EmbeddingService()

# Made with Bob
