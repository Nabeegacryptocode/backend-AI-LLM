"""
LLM Service for interacting with OpenAI API
"""
import openai
from typing import Optional, Dict, Any, List
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM operations using OpenAI API"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        openai.api_key = settings.OPENAI_API_KEY
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.embedding_model = settings.EMBEDDING_MODEL
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            logger.debug(f"Generating embedding for text: {text[:100]}...")
            
            response = await openai.Embedding.acreate(
                model=self.embedding_model,
                input=text
            )
            
            embedding = response['data'][0]['embedding']
            logger.debug(f"Generated embedding with dimension: {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_response(
        self,
        question: str,
        context: str,
        conversation_id: Optional[str] = None,
        max_tokens: int = 1000,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate response using RAG
        
        Args:
            question: User's question
            context: Retrieved context from documents
            conversation_id: Optional conversation ID
            max_tokens: Maximum tokens in response
            conversation_history: Optional conversation history
            
        Returns:
            Dictionary with answer, conversation_id, and tokens_used
        """
        try:
            logger.info(f"Generating response for question: {question[:100]}...")
            
            # System prompt
            system_prompt = """You are an expert assistant for IBM documentation. 
Your role is to provide accurate, helpful answers based on the provided context from IBM documentation.

Guidelines:
- Answer questions based ONLY on the provided context
- If the answer is not in the context, clearly state that you don't have that information
- Provide detailed, technical answers with examples when appropriate
- Always cite the source documentation when possible
- Use clear, professional language
- If the question is ambiguous, ask for clarification
- Format code examples properly with markdown code blocks
"""
            
            # User prompt with context
            user_prompt = f"""Context from IBM Documentation:
{context}

Question: {question}

Please provide a detailed answer based on the context above. If the context doesn't contain enough information to answer the question, please say so clearly."""
            
            # Build messages
            messages = [
                {"role": "system", "content": system_prompt}
            ]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current question
            messages.append({"role": "user", "content": user_prompt})
            
            # Generate response
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=max_tokens
            )
            
            answer = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            logger.info(f"Generated response with {tokens_used} tokens")
            
            return {
                "answer": answer,
                "conversation_id": conversation_id or response.id,
                "tokens_used": tokens_used
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts")
            
            response = await openai.Embedding.acreate(
                model=self.embedding_model,
                input=texts
            )
            
            embeddings = [item['embedding'] for item in response['data']]
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.model)
            return len(encoding.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens: {str(e)}")
            # Rough estimate: 1 token ≈ 4 characters
            return len(text) // 4


# Global instance
llm_service = LLMService()

# Made with Bob
