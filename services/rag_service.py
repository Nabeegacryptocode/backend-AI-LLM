"""
RAG (Retrieval Augmented Generation) Service
Combines vector search with LLM generation
"""
from typing import List, Dict, Any, Optional
import logging

from services.embedding_service import embedding_service
from services.llm_service import llm_service
from app.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG pipeline operations"""
    
    def __init__(self):
        """Initialize RAG service"""
        self.embedding_service = embedding_service
        self.llm_service = llm_service
    
    async def generate_answer(
        self,
        question: str,
        conversation_id: Optional[str] = None,
        max_tokens: int = 1000,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        namespace: str = "",
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate answer using RAG pipeline
        
        Args:
            question: User's question
            conversation_id: Optional conversation ID
            max_tokens: Maximum tokens in response
            conversation_history: Optional conversation history
            namespace: Optional namespace to search in
            filter_dict: Optional metadata filter
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        try:
            logger.info(f"Processing RAG request: {question[:100]}...")
            
            # Step 1: Retrieve relevant documents
            similar_docs = await self.embedding_service.search_similar(
                query=question,
                top_k=settings.TOP_K_RESULTS,
                namespace=namespace,
                filter_dict=filter_dict
            )
            
            if not similar_docs:
                logger.warning("No relevant documents found")
                return {
                    "answer": "I couldn't find any relevant information in the IBM documentation to answer your question. Please try rephrasing your question or ask about a different topic.",
                    "sources": [],
                    "conversation_id": conversation_id or "no-context",
                    "tokens_used": 0,
                    "retrieved_docs": 0
                }
            
            # Step 2: Build context from retrieved documents
            context = self._build_context(similar_docs)
            
            logger.info(f"Built context from {len(similar_docs)} documents")
            
            # Step 3: Generate response using LLM
            response = await self.llm_service.generate_response(
                question=question,
                context=context,
                conversation_id=conversation_id,
                max_tokens=max_tokens,
                conversation_history=conversation_history
            )
            
            # Step 4: Format sources
            sources = self._format_sources(similar_docs)
            
            logger.info(f"Generated answer with {response['tokens_used']} tokens")
            
            return {
                "answer": response["answer"],
                "sources": sources,
                "conversation_id": response["conversation_id"],
                "tokens_used": response["tokens_used"],
                "retrieved_docs": len(similar_docs)
            }
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {str(e)}")
            raise
    
    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Build context string from retrieved documents
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            metadata = doc.get("metadata", {})
            content = doc.get("content", "")
            title = metadata.get("title", "Unknown")
            url = metadata.get("url", "")
            source_type = metadata.get("source_type", "IBM Documentation")
            
            # Format each document section
            section = f"""
Document {i}: {title}
Source: {source_type}
URL: {url}
Relevance Score: {doc.get('score', 0):.2f}

Content:
{content}

---
"""
            context_parts.append(section)
        
        return "\n".join(context_parts)
    
    def _format_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format source documents for response
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            List of formatted source dictionaries
        """
        sources = []
        
        for doc in documents:
            metadata = doc.get("metadata", {})
            content = doc.get("content", "")
            
            # Truncate content for preview
            content_preview = content[:200] + "..." if len(content) > 200 else content
            
            sources.append({
                "title": metadata.get("title", "Unknown"),
                "url": metadata.get("url", ""),
                "content": content_preview,
                "relevance_score": doc.get("score", 0),
                "source_type": metadata.get("source_type", "IBM Documentation")
            })
        
        return sources
    
    async def get_context_for_question(
        self,
        question: str,
        top_k: int = None,
        namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Get relevant context for a question without generating answer
        Useful for debugging and testing
        
        Args:
            question: User's question
            top_k: Number of documents to retrieve
            namespace: Optional namespace
            
        Returns:
            Retrieved documents and context
        """
        try:
            # Retrieve relevant documents
            similar_docs = await self.embedding_service.search_similar(
                query=question,
                top_k=top_k or settings.TOP_K_RESULTS,
                namespace=namespace
            )
            
            # Build context
            context = self._build_context(similar_docs)
            
            return {
                "question": question,
                "context": context,
                "documents": similar_docs,
                "document_count": len(similar_docs)
            }
            
        except Exception as e:
            logger.error(f"Error getting context: {str(e)}")
            raise


# Global instance
rag_service = RAGService()

# Made with Bob
