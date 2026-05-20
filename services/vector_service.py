"""
Vector Database Service for Pinecone integration
"""
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from backend.app.config import settings

logger = logging.getLogger(__name__)


class VectorService:
    """Service for vector database operations using Pinecone"""
    
    def __init__(self):
        """Initialize Pinecone client"""
        self.initialized = False
        self.pc = None
        self.index = None
        self.index_name = settings.PINECONE_INDEX_NAME
        
    def initialize(self):
        """Initialize Pinecone connection"""
        if self.initialized:
            return
            
        try:
            logger.info("Initializing Pinecone connection")
            
            # Initialize Pinecone client with new API
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Check if index exists
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.warning(f"Index {self.index_name} does not exist. Creating it...")
                self.create_index()
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            self.initialized = True
            
            logger.info(f"Successfully connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Error initializing Pinecone: {str(e)}")
            raise
    
    def create_index(self):
        """Create Pinecone index if it doesn't exist"""
        try:
            logger.info(f"Creating Pinecone index: {self.index_name}")
            
            # Use ServerlessSpec for serverless indexes
            self.pc.create_index(
                name=self.index_name,
                dimension=settings.EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=settings.PINECONE_CLOUD or "aws",
                    region=settings.PINECONE_ENVIRONMENT
                )
            )
            
            logger.info(f"Index {self.index_name} created successfully")
            
        except Exception as e:
            logger.error(f"Error creating index: {str(e)}")
            raise
    
    async def upsert_vectors(
        self,
        vectors: List[Dict[str, Any]],
        namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Upsert vectors to Pinecone
        
        Args:
            vectors: List of vector dictionaries with id, values, and metadata
            namespace: Optional namespace for organization
            
        Returns:
            Upsert response
        """
        if not self.initialized:
            self.initialize()
        
        try:
            logger.info(f"Upserting {len(vectors)} vectors to Pinecone")
            
            # Format vectors for Pinecone
            formatted_vectors = []
            for vec in vectors:
                formatted_vectors.append({
                    "id": vec["id"],
                    "values": vec["values"],
                    "metadata": vec.get("metadata", {})
                })
            
            # Upsert in batches of 100
            batch_size = 100
            total_upserted = 0
            
            for i in range(0, len(formatted_vectors), batch_size):
                batch = formatted_vectors[i:i + batch_size]
                response = self.index.upsert(
                    vectors=batch,
                    namespace=namespace
                )
                total_upserted += response.get("upserted_count", len(batch))
            
            logger.info(f"Successfully upserted {total_upserted} vectors")
            
            return {
                "upserted_count": total_upserted,
                "namespace": namespace
            }
            
        except Exception as e:
            logger.error(f"Error upserting vectors: {str(e)}")
            raise
    
    async def search(
        self,
        query_vector: List[float],
        top_k: int = None,
        namespace: str = "",
        filter_dict: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            namespace: Optional namespace to search in
            filter_dict: Optional metadata filter
            include_metadata: Whether to include metadata in results
            
        Returns:
            List of matching documents with scores
        """
        if not self.initialized:
            self.initialize()
        
        try:
            top_k = top_k or settings.TOP_K_RESULTS
            
            logger.info(f"Searching for top {top_k} similar vectors")
            
            # Query Pinecone
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                namespace=namespace,
                filter=filter_dict,
                include_metadata=include_metadata
            )
            
            # Format results
            matches = []
            for match in results.get("matches", []):
                # Only include results above minimum relevance score
                if match.get("score", 0) >= settings.MIN_RELEVANCE_SCORE:
                    matches.append({
                        "id": match["id"],
                        "score": match["score"],
                        "metadata": match.get("metadata", {}),
                        "content": match.get("metadata", {}).get("content", "")
                    })
            
            logger.info(f"Found {len(matches)} matches above threshold")
            
            return matches
            
        except Exception as e:
            logger.error(f"Error searching vectors: {str(e)}")
            raise
    
    async def delete_vectors(
        self,
        ids: List[str],
        namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Delete vectors by IDs
        
        Args:
            ids: List of vector IDs to delete
            namespace: Optional namespace
            
        Returns:
            Delete response
        """
        if not self.initialized:
            self.initialize()
        
        try:
            logger.info(f"Deleting {len(ids)} vectors from Pinecone")
            
            self.index.delete(
                ids=ids,
                namespace=namespace
            )
            
            logger.info(f"Successfully deleted {len(ids)} vectors")
            
            return {
                "deleted_count": len(ids),
                "namespace": namespace
            }
            
        except Exception as e:
            logger.error(f"Error deleting vectors: {str(e)}")
            raise
    
    async def delete_all(self, namespace: str = ""):
        """
        Delete all vectors in a namespace
        
        Args:
            namespace: Namespace to clear
        """
        if not self.initialized:
            self.initialize()
        
        try:
            logger.warning(f"Deleting all vectors in namespace: {namespace or 'default'}")
            
            self.index.delete(
                delete_all=True,
                namespace=namespace
            )
            
            logger.info("Successfully deleted all vectors")
            
        except Exception as e:
            logger.error(f"Error deleting all vectors: {str(e)}")
            raise
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """
        Get index statistics
        
        Returns:
            Index statistics
        """
        if not self.initialized:
            self.initialize()
        
        try:
            stats = self.index.describe_index_stats()
            
            return {
                "total_vector_count": stats.get("total_vector_count", 0),
                "dimension": stats.get("dimension", 0),
                "index_fullness": stats.get("index_fullness", 0),
                "namespaces": stats.get("namespaces", {})
            }
            
        except Exception as e:
            logger.error(f"Error getting index stats: {str(e)}")
            raise
    
    async def fetch_vectors(
        self,
        ids: List[str],
        namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Fetch vectors by IDs
        
        Args:
            ids: List of vector IDs to fetch
            namespace: Optional namespace
            
        Returns:
            Dictionary of vectors
        """
        if not self.initialized:
            self.initialize()
        
        try:
            logger.info(f"Fetching {len(ids)} vectors from Pinecone")
            
            response = self.index.fetch(
                ids=ids,
                namespace=namespace
            )
            
            return response.get("vectors", {})
            
        except Exception as e:
            logger.error(f"Error fetching vectors: {str(e)}")
            raise


# Global instance
vector_service = VectorService()

# Made with Bob
