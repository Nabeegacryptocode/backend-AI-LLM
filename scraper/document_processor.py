"""
Document processing and chunking utilities
"""
from typing import List, Dict, Any
import re
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process and chunk documents for embedding"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean text content
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-\'"]+', '', text)
        
        # Remove multiple periods
        text = re.sub(r'\.{2,}', '.', text)
        
        return text.strip()
    
    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> List[str]:
        """
        Split text into chunks with overlap
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or settings.CHUNK_SIZE
        chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Get chunk
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size * 0.5:  # Only break if we're past halfway
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            
            # Move start position with overlap
            start = end - chunk_overlap
            
            # Prevent infinite loop
            if start >= len(text):
                break
        
        return chunks
    
    @staticmethod
    def chunk_document(
        content: str,
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> List[str]:
        """
        Process and chunk a document
        
        Args:
            content: Document content
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of processed chunks
        """
        # Clean text
        cleaned = DocumentProcessor.clean_text(content)
        
        # Chunk text
        chunks = DocumentProcessor.chunk_text(
            cleaned,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        logger.info(f"Created {len(chunks)} chunks from document")
        
        return chunks
    
    @staticmethod
    def create_chunks_with_metadata(
        document: Dict[str, Any],
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> List[Dict[str, Any]]:
        """
        Create chunks with metadata from a document
        
        Args:
            document: Document dictionary with content and metadata
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of chunk dictionaries with metadata
        """
        content = document.get('content', '')
        base_metadata = document.get('metadata', {})
        
        # Create chunks
        chunks = DocumentProcessor.chunk_document(
            content,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Create chunk documents
        chunk_docs = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                'chunk_index': i,
                'total_chunks': len(chunks),
                'chunk_size': len(chunk)
            })
            
            chunk_docs.append({
                'content': chunk,
                'metadata': chunk_metadata
            })
        
        return chunk_docs
    
    @staticmethod
    def extract_sections(text: str) -> List[Dict[str, str]]:
        """
        Extract sections from text based on headers
        
        Args:
            text: Text with headers
            
        Returns:
            List of sections with titles and content
        """
        sections = []
        
        # Split by headers (lines that look like titles)
        lines = text.split('\n')
        current_section = {'title': '', 'content': []}
        
        for line in lines:
            line = line.strip()
            
            # Check if line is a header (short, capitalized, or ends with colon)
            if (len(line) < 100 and 
                (line.isupper() or 
                 line.endswith(':') or
                 (line and line[0].isupper() and not line.endswith('.')))):
                
                # Save previous section
                if current_section['content']:
                    sections.append({
                        'title': current_section['title'],
                        'content': '\n'.join(current_section['content'])
                    })
                
                # Start new section
                current_section = {
                    'title': line.rstrip(':'),
                    'content': []
                }
            else:
                if line:
                    current_section['content'].append(line)
        
        # Add last section
        if current_section['content']:
            sections.append({
                'title': current_section['title'],
                'content': '\n'.join(current_section['content'])
            })
        
        return sections
    
    @staticmethod
    def merge_short_chunks(
        chunks: List[str],
        min_size: int = 200
    ) -> List[str]:
        """
        Merge chunks that are too short
        
        Args:
            chunks: List of chunks
            min_size: Minimum chunk size
            
        Returns:
            List of merged chunks
        """
        if not chunks:
            return []
        
        merged = []
        current = chunks[0]
        
        for chunk in chunks[1:]:
            if len(current) < min_size:
                current += ' ' + chunk
            else:
                merged.append(current)
                current = chunk
        
        # Add last chunk
        if current:
            merged.append(current)
        
        return merged

# Made with Bob
