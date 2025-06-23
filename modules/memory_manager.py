"""
Memory Manager Module

Handles storage and retrieval of research information using ChromaDB
for vector similarity search and metadata storage.
"""

import chromadb
import hashlib
import json
from typing import List, Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)

class MemoryManager:
    """Manage research memory with vector storage and retrieval"""
    
    def __init__(self, config, collection_name: str = "research_memory"):
        self.config = config
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        self.client = chromadb.Client()
        
        # Use simple text-based embeddings for now
        self.embedding_model = None
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Research agent memory storage"}
        )
        
        logger.info(f"Initialized memory manager with collection: {collection_name}")
    
    def store_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Store documents in memory with embeddings
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            List of document IDs that were stored
        """
        if not documents:
            return []
        
        logger.info(f"Storing {len(documents)} documents in memory")
        
        stored_ids = []
        
        for doc in documents:
            try:
                # Generate unique ID for document
                doc_id = self._generate_document_id(doc)
                
                # Check if document already exists
                if self._document_exists(doc_id):
                    logger.debug(f"Document {doc_id} already exists, skipping")
                    stored_ids.append(doc_id)
                    continue
                
                # Prepare content for embedding
                content = self._prepare_content_for_embedding(doc)
                
                if not content:
                    logger.warning(f"No content to embed for document: {doc.get('title', 'Unknown')}")
                    continue
                
                # Generate simple hash-based embedding for now
                embedding = self._generate_simple_embedding(content)
                
                # Prepare metadata
                metadata = self._prepare_metadata(doc)
                
                # Store in ChromaDB
                self.collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[content],
                    metadatas=[metadata]
                )
                
                stored_ids.append(doc_id)
                logger.debug(f"Stored document: {doc.get('title', doc_id)}")
                
            except Exception as e:
                logger.error(f"Failed to store document {doc.get('title', 'Unknown')}: {str(e)}")
                continue
        
        logger.info(f"Successfully stored {len(stored_ids)} documents")
        return stored_ids
    
    def search_similar(self, query: str, top_k: int = 5, filter_metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents based on query
        
        Args:
            query: Search query
            top_k: Number of top results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of similar documents with scores
        """
        logger.info(f"Searching for similar documents: {query[:50]}...")
        
        try:
            # Generate simple hash-based embedding for query
            query_embedding = self._generate_simple_embedding(query)
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_metadata
            )
            
            # Format results
            formatted_results = []
            
            if results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    formatted_results.append({
                        'id': doc_id,
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity_score': 1 - results['distances'][0][i] if results['distances'][0] else 0.0
                    })
            
            logger.info(f"Found {len(formatted_results)} similar documents")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Memory search failed: {str(e)}")
            return []
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific document by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document data or None if not found
        """
        try:
            results = self.collection.get(ids=[doc_id])
            
            if results['ids'] and results['ids'][0]:
                return {
                    'id': results['ids'][0],
                    'content': results['documents'][0],
                    'metadata': results['metadatas'][0]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve document {doc_id}: {str(e)}")
            return None
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored memory
        
        Returns:
            Dictionary with memory statistics
        """
        try:
            count = self.collection.count()
            
            # Get sample of documents to analyze
            sample_results = self.collection.get(limit=100)
            
            source_types = {}
            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    source_type = metadata.get('source_type', 'unknown')
                    source_types[source_type] = source_types.get(source_type, 0) + 1
            
            return {
                'total_documents': count,
                'source_types': source_types,
                'collection_name': self.collection_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {str(e)}")
            return {'total_documents': 0, 'source_types': {}, 'collection_name': self.collection_name}
    
    def clear_memory(self) -> bool:
        """
        Clear all documents from memory
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete the collection
            self.client.delete_collection(self.collection_name)
            
            # Recreate the collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Research agent memory storage"}
            )
            
            logger.info("Memory cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear memory: {str(e)}")
            return False
    
    def _generate_document_id(self, doc: Dict[str, Any]) -> str:
        """Generate unique ID for a document"""
        # Use URL if available, otherwise use title + content hash
        if doc.get('url'):
            return hashlib.md5(doc['url'].encode()).hexdigest()
        
        content_for_id = (doc.get('title', '') + doc.get('content', ''))[:1000]
        return hashlib.md5(content_for_id.encode()).hexdigest()
    
    def _document_exists(self, doc_id: str) -> bool:
        """Check if document already exists in memory"""
        try:
            results = self.collection.get(ids=[doc_id])
            return bool(results['ids'])
        except:
            return False
    
    def _prepare_content_for_embedding(self, doc: Dict[str, Any]) -> str:
        """Prepare document content for embedding"""
        parts = []
        
        # Add title
        if doc.get('title'):
            parts.append(f"Title: {doc['title']}")
        
        # Add main content
        if doc.get('content'):
            content = doc['content']
            # Limit content length for embedding
            if len(content) > 2000:
                content = content[:2000] + "..."
            parts.append(f"Content: {content}")
        
        # Add abstract for academic papers
        if doc.get('abstract'):
            parts.append(f"Abstract: {doc['abstract']}")
        
        return "\n\n".join(parts)
    
    def _prepare_metadata(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare metadata for storage"""
        metadata = {
            'title': doc.get('title', ''),
            'url': doc.get('url', ''),
            'source_type': doc.get('source_type', 'unknown'),
            'retrieved_at': doc.get('retrieved_at', ''),
        }
        
        # Add academic paper specific metadata
        if doc.get('authors'):
            metadata['authors'] = json.dumps(doc['authors'])
        
        if doc.get('published'):
            metadata['published'] = doc['published']
        
        if doc.get('categories'):
            metadata['categories'] = json.dumps(doc['categories'])
        
        # Ensure all values are strings (ChromaDB requirement)
        for key, value in metadata.items():
            if value is None:
                metadata[key] = ''
            elif not isinstance(value, str):
                metadata[key] = str(value)
        
        return metadata
    
    def _generate_simple_embedding(self, text: str) -> List[float]:
        """Generate a simple embedding based on text characteristics"""
        # This is a simplified embedding approach
        # In production, you'd want to use proper sentence transformers
        
        # Convert text to lowercase and get basic features
        text = text.lower()
        
        # Create a 384-dimensional vector (similar to sentence transformers)
        embedding = [0.0] * 384
        
        # Use text characteristics to populate embedding
        words = text.split()
        
        if words:
            # Use word count and length features
            word_count = len(words)
            avg_word_length = sum(len(word) for word in words) / len(words)
            
            # Simple hash-based features
            for i, word in enumerate(words[:50]):  # Use first 50 words
                word_hash = hash(word) % 384
                embedding[word_hash] += 1.0 / (i + 1)  # Weighted by position
            
            # Normalize the embedding
            magnitude = sum(x * x for x in embedding) ** 0.5
            if magnitude > 0:
                embedding = [x / magnitude for x in embedding]
        
        return embedding
