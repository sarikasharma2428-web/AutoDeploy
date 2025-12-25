import logging
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

from config import settings

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        self.dimension = settings.EMBEDDING_DIMENSION
        self.model = None
        self._load_model()
    
    def _load_model(self):
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Using device: {device}")
            
            self.model = SentenceTransformer(self.model_name, device=device)
            
            logger.info(f"Model loaded successfully. Embedding dimension: {self.dimension}")
        
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def generate_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        if not chunks:
            return []
        
        texts = [self._prepare_text(chunk) for chunk in chunks]
        
        embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            
            try:
                batch_embeddings = self.model.encode(
                    batch_texts,
                    batch_size=self.batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )
                embeddings.extend(batch_embeddings)
                
                if (i + self.batch_size) % 100 == 0:
                    logger.info(f"Processed {i + self.batch_size}/{len(texts)} chunks")
            
            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i}: {e}")
                batch_embeddings = [np.zeros(self.dimension) for _ in batch_texts]
                embeddings.extend(batch_embeddings)
        
        enriched_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            enriched_chunk = chunk.copy()
            enriched_chunk['embedding'] = embedding.tolist()
            enriched_chunks.append(enriched_chunk)
        
        logger.info(f"Successfully generated embeddings for {len(enriched_chunks)} chunks")
        
        return enriched_chunks
    
    def _prepare_text(self, chunk: Dict) -> str:
        content = chunk.get('content', '')
        file_path = chunk.get('file_path', '')
        language = chunk.get('language', '')
        chunk_type = chunk.get('type', '')
        
        context = f"File: {file_path}\nLanguage: {language}\nType: {chunk_type}\n\nCode:\n{content}"
        
        max_length = 512
        if len(context) > max_length:
            context = context[:max_length]
        
        return context
    
    def generate_single_embedding(self, text: str) -> List[float]:
        try:
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating single embedding: {e}")
            return [0.0] * self.dimension
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        return float(similarity)
    
    def get_model_info(self) -> Dict:
        return {
            'model_name': self.model_name,
            'dimension': self.dimension,
            'batch_size': self.batch_size,
            'device': 'cuda' if torch.cuda.is_available() else 'cpu'
        }